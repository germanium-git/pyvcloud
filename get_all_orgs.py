#!/usr/bin/env python3

"""
===================================================================================================
   Author:         Petr Nemec
   Description:    Illustrates how to list all Organizations
   Date:           2018-01-14
===================================================================================================
"""


from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from prettytable import PrettyTable
import os
from termcolor import cprint
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Update with valid vCD's URL or IP address
client = Client(os.environ['VCD_IP'],
                api_version='31.0',
                verify_ssl_certs=False,
                log_file='pyvcloud.log',
                log_requests=True,
                log_headers=True,
                log_bodies=True)

# Update with valid administrator's credentials
client.set_credentials(BasicLoginCredentials(os.environ['VCD_USER'], 'SYSTEM', os.environ['VCD_PASSWORD']))


# Check if current used is system admin
if not client.is_sysadmin():
    print("The current user is not system admin, can't manage all Organizations")
else:
    orgtable = PrettyTable(["Organization name", "href"])
    orgs = client.get_org_list()
    for o in orgs:
        # print(o.attrib['name'])
        # print(o.get('name'))
        # print(o.get('href'))
        orgtable.add_row([o.get('name'), o.get('href')])
    cprint('Print all Organizations', 'yellow')
    print(orgtable)

# Log out.
print("Logging out")
client.logout()
