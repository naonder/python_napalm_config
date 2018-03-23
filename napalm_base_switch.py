#!/usr/bin/env python3

# To be used to configure a baseline access switch config as well as MGMT VLAN SVI and uplink ports
# Still need to update to support YAML w/ Jinja templating
# Perhaps combine all 3 types (router, core, switch) into a single program

import napalm
import json

with open("/path/to/basecreds.json") as credentials:
    creds = json.load(credentials)

name = creds["username"]
passwrd = creds["password"]

driver = napalm.get_network_driver("ios")
device_address = input('Input device address to send config to: ')
device = driver(device_address, name, passwrd)
device.open()

device.load_merge_candidate(filename='/path/to/baseswitch.txt')
print(device.compare_config())
print('Committing device config now....')
device.commit_config()
print('Finished sending device config, exiting...')

device.close()
credentials.close()
