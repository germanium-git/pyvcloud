#!/usr/bin/env python3

"""
===================================================================================================
    Author:          Petr Nemec
    Description:     It creates the isolated Org VDC network

    Date:            2019-03-25


    TODO DHCP service can't be disabled when new network is being deployed
===================================================================================================
"""

import requests
import sys

#sys.path.append("D:\MEGA\Github\pyvcloud\pyvcloud")

from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC


# Private utility functions.
from tenantlib import handle_task

from vcdconfig import Config


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
print("Fetching org...")
try:
    # This call gets a record that we can turn into an Org class.
    org_record = client.get_org_by_name(cfg.org.name)
    org = Org(client, href=org_record.get('href'))
    print("Org already exists: {0}".format(org.get_name()))
except Exception:
    print("Org does not exist, exiting")
    sys.exit()


# Ensure VDC exists.
print("Fetching VDC...")
try:
    vdc_resource = org.get_vdc(cfg.org.vdc_name)
    vdc = VDC(client, resource=vdc_resource)
    print("VDC already exists: {0}".format(cfg.org.vdc_name))
except Exception:
    print("VDC {0} does not exist, exiting".format(cfg.org['vdc_name']))
    sys.exit()


# Ensure Isolated Org Network doesn't exist.
print("Fetching Network...")
try:
    network_resource = vdc.get_isolated_orgvdc_network(cfg.org.org_isol_nw.name)
    print("Network already exists: {0}".format(cfg.org.org_isol_nw.name))
except Exception:
    print("Network {0} does not exist, creating".format(cfg.org.org_isol_nw.name))
    network_resource = vdc.create_isolated_vdc_network(network_name=cfg.org.org_isol_nw.name,
                                                       network_cidr=cfg.org.org_isol_nw.cidr,
                                                       is_dhcp_enabled=False,
                                                       is_shared=cfg.org.org_isol_nw.is_shared)

    handle_task(client, network_resource.Tasks.Task[0])


# Final report ------------------------------------------------------------------------------------
new_isolated_network = vdc.get_isolated_orgvdc_network(cfg.org.org_isol_nw.name)
print('\nNew Isolated network is created -------------------------------------------------')
print('name: {}'.format(new_isolated_network.attrib['name']))
print('href: {}'.format(new_isolated_network.attrib['href']))
