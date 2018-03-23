#!/usr/bin/env python3
'''This will allow one to add or modify an existing BGP configuration on a Cisco device utilizing NAPALM
   This is also a work in progress'''
import napalm
import json
import pprint
import jinja2
import yaml

config_file = open('/path/to/bgp_config.txt', 'w')

# Determine if we'll be using in a VRF or not. This will decide which template and yaml file to use
while True:
    selection = input('\r\nChoose BGP type (global or VRF)' '\r\n1-Global' '\r\n2-VRF' '\r\nInput here: ')
    if selection == '1':
        template_file = 'bgp.j2'
        config_template = '/path/to/bgp.yaml'
        break
    elif selection == '2':
        template_file = 'bgpvrf.j2'
        config_template = '/path/to/bgpvrf.yaml'
        break
    else:
        print('Choose 1 or 2')

# Load yaml data and jinja2 template. From that write to the config file which will be pushed to a device
config_data = yaml.load(open(config_template))
env = jinja2.Environment(loader=jinja2.FileSystemLoader('/path/to/'), trim_blocks=True,
                         lstrip_blocks=True)
template = env.get_template(template_file)
config_file.write(template.render(config_data))
config_file.close()

# Prompt for device address/hostname, connect to it, and show current BGP neighbors
with open('/path/to/basecreds.json') as credentials:
    creds = json.load(credentials)
name = creds['username']
passwrd = creds['password']
device_address = input('\r\nInput device address to send config to: ')
driver = napalm.get_network_driver("ios")
device = driver(device_address, name, passwrd)
print('\r\nConnecting to device and will display current BGP neighbors...')
device.open()
try:
    pprint.pprint(device.get_bgp_neighbors())
    
# Catch-all except clause. Still need to get the specific error instead
except:
    print('\r\nNo current BGP config exists, continuing...')
    pass

# Load the config file and print the diff. Then prompt to either commit or discard changes.
print('\r\nLoading new config...')
device.load_merge_candidate(filename='/path/to/bgp_config.txt')
print('\r\nCONFIG DIFF:')
print(device.compare_config())
while True:
    choice = input('\r\nWould you like to commit these changes? [y|n]: ')
    if choice.lower() == 'y':
        print('\r\nCommitting changes...')
        device.commit_config()
        break
    elif choice.lower() == 'n':
        print('\r\nDiscarding changes...')
        device.discard_config()
        break
    else:
        print('Choose either "y" or "n"')

# Create 2 lists that neighbor addresses can get added to if there is a route-map or prefix-list change
neighbor_in = []
neighbor_out = []

for peer in config_data['neighbors']:
    
    if 'route_map_in' in peer:
        if peer['route_map_in'] is not None:
            neighbor_in.append(peer['neighbor'])
    elif 'no_route_map_in' in peer:
        if peer['no_route_map_in'] is not None:
            neighbor_in.append(peer['neighbor'])
    elif 'prefix_list_in' in peer:
        if peer['prefix_list_in'] is not None:
            neighbor_in.append(peer['neighbor'])
    elif 'no_prefix_list_in' in peer:
        if peer['no_prefix_list_in'] is not None:
            neighbor_in.append(peer['neighbor'])
    elif 'route_map_in' in peer:
        if peer['route_map_in'] is not None:
            neighbor_in.append(peer['neighbor'])

for peer in config_data['neighbors']:
    
    if 'route_map_out' in peer:
        if peer['route_map_out'] is not None:
            neighbor_out.append(peer['neighbor'])
    elif 'no_route_map_out' in peer:
        if peer['no_route_map_out'] is not None:
            neighbor_out.append(peer['neighbor'])
    elif 'prefix_list_out' in peer:
        if peer['prefix_list_out'] is not None:
            neighbor_out.append(peer['neighbor'])
    elif 'no_prefix_list_out' in peer:
        if peer['no_prefix_list_out'] is not None:
            neighbor_out.append(peer['neighbor'])

# If lists aren't blank, then will issue either in or out soft clearing
for neighbor in neighbor_in:
    print('Clearing soft inbound for neighbor {}'.format(neighbor))
    device.cli(['clear ip bgp {} soft in'.format(neighbor)])
for neighbor in neighbor_out:
    print('Clearing soft outbound for neighbor {}'.format(neighbor))
    device.cli(['clear ip bgp {} soft out'.format(neighbor)])

# Print the BGP neighbor info.
pprint.pprint(device.get_bgp_neighbors())

# Disconnect from the device and finish.
device.close()
print('\r\nBGP configuration is completed')
