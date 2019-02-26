#!/usr/bin/env python3

"""
===================================================================================================
   Author:          Petr Nemec
   Description:     Cleanup script to wipe out the components created by other scripts
                    - isolated networks
                    - routed network
                    - edge gateway
                    - external network

   Date:            2019-00-26
===================================================================================================
"""

import requests
import sys
import time

from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.platform import Platform
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC

from vcdconfig import Config

# Private utility functions.
from tenantlib import handle_task


# cfg = Config.load()
cfg = Config.load(data='config_nogit.yml')


# Disable warnings from self-signed certificates.
requests.packages.urllib3.disable_warnings()

# Login. SSL certificate verification is turned off to allow self-signed --------------------------
# certificates.  You should only do this in trusted environments.
print("Logging in...")
client = Client(cfg.vcd.host,
                verify_ssl_certs=cfg.connection.verify,
                log_file=cfg.logging.default_log_filename,
                log_requests=cfg.logging.log_requests,
                log_headers=cfg.logging.log_headers,
                log_bodies=cfg.logging.log_bodies)


client.set_highest_supported_version()
client.set_credentials(BasicLoginCredentials(cfg.vcd.sys_admin_username,
                                             cfg.vcd.sys_org_name,
                                             cfg.vcd.sys_admin_pass))


# Ensure the org exists.
print("Fetching the organization...")
try:
    # This call gets a record that we can turn into an Org class.
    org_record = client.get_org_by_name(cfg.org.name)
    org = Org(client, href=org_record.get('href'))
    print("The organization {0} has been found".format(org.get_name()))
except Exception:
    print("The organization {0} does not exist, exiting".format(org.get_name()))
    sys.exit()


# Ensure VDC exists.
print("Fetching the VDC...")
try:
    vdc_resource = org.get_vdc(cfg.org.vdc_name)
    vdc = VDC(client, resource=vdc_resource)
    print("The VDC {0} has been found".format(cfg.org.vdc_name))
except Exception:
    print("The VDC {0} does not exist, exiting".format(cfg.org['vdc_name']))
    sys.exit()


# Ensure Isolated Org Network exists and delete it. -----------------------------------------------
print("\nFetching the isolated network...")
try:
    network_resource = vdc.get_isolated_orgvdc_network(cfg.org.org_isol_nw.name)
    print("The isolated network {0} exists, deleting.".format(cfg.org.org_isol_nw.name))
    vdc.delete_isolated_orgvdc_network(cfg.org.org_isol_nw.name)
except Exception:
    print("The isolated network {0} does not exist.".format(cfg.org.org_isol_nw.name))


# Ensure Routed Org Network doesn't exist and delete it. ------------------------------------------
print("\nFetching the routed network {0} ...".format(cfg.org.org_routed_nw.name))
try:
    routed_network = vdc.get_routed_orgvdc_network(cfg.org.org_routed_nw.name)
    print("The routed network {0} exists, deleting".format(cfg.org.org_routed_nw.name))
    # print('name: {}'.format(routed_network.attrib['name']))
    # print('href: {}'.format(routed_network.attrib['href']))
    delete_nw = vdc.delete_routed_orgvdc_network(cfg.org.org_routed_nw.name)
    # Test whether it's been deleted
    i = 0
    while i < 60:
        obj = client.get_resource(delete_nw.attrib['href'])
        if obj.attrib['status'] != 'success':
            print(obj.attrib['status'])
            i += 1
            time.sleep(1)
        else:
            print("The network {0} doesn't exist".format(cfg.org.org_routed_nw.name))
            i = 61

except Exception:
    print("The routed network {0} does not exist".format(cfg.org.org_routed_nw.name))


# Ensure the Edge gateway doesn't exist and delete it. --------------------------------------------
print("\nFetching Edges...")
try:
    network_resource = vdc.get_gateway(cfg.org.edge_gateway.name)
    print("Edge gateway exists: {0}, deleting".format(cfg.org.edge_gateway.name))
    delete_edge = vdc.delete_gateway(cfg.org.edge_gateway.name)
    # Test whether it's been deleted
    i = 0
    while i < 60:
        obj = client.get_resource(delete_edge.attrib['href'])
        if obj.attrib['status'] != 'success':
            print(obj.attrib['status'])
            i += 1
            time.sleep(1)
        else:
            print("The edge {0} doesn't exist".format(cfg.org.edge_gateway.name))
            i = 61

except Exception:
    print("The Edge gateway {0} does not exist".format(cfg.org.edge_gateway.name))


# Create an instance of the Class Platform --------------------------------------------------------
platform = Platform(client)

# Ensure External Network exists and delete it ----------------------------------------------------
print("\nFetching the external network...")
try:
    network_resource = platform.get_external_network(cfg.system.ext_network.name)
    print("The external network {0} exists, deleting".format(cfg.system.ext_network.name))
    platform.delete_external_network(cfg.system.ext_network.name)
except Exception:
    print("The external network {0} does not exist.".format(cfg.system.ext_network.name))
