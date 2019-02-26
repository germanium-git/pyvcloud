#!/usr/bin/env python3

"""
===================================================================================================
   Author:          Petr Nemec
   Description:     It creates edge gateway with enabled DLR

   Date:            2019-00-26
===================================================================================================
"""


import requests
import sys

from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC

from pyvcloud.vcd.client import GatewayBackingConfigType

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

# Ensure the org exists. --------------------------------------------------------------------------
print("Fetching org...")
try:
    # This call gets a record that we can turn into an Org class.
    org_record = client.get_org_by_name(cfg.org.name)
    org = Org(client, href=org_record.get('href'))
    print("Org already exists: {0}".format(org.get_name()))
except Exception:
    print("Org does not exist, exiting")
    sys.exit()


# Ensure VDC exists. ------------------------------------------------------------------------------
print("Fetching VDC...")
try:
    vdc_resource = org.get_vdc(cfg.org.vdc_name)
    vdc = VDC(client, resource=vdc_resource)
    print("VDC already exists: {0}".format(cfg.org.vdc_name))
except Exception:
    print("VDC {0} does not exist, exiting".format(cfg.org['vdc_name']))
    sys.exit()


# Ensure the edge doesn't exist. ------------------------------------------------------------------
print("Fetching Edges...")
try:
    network_resource = vdc.get_gateway(cfg.org.edge_gateway.name)
    print("Edge gateway already exists: {0}".format(cfg.org.edge_gateway.name))
except Exception:
    print("Edge gateway {0} does not exist, creating".format(cfg.org.edge_gateway.name))
    network_resource = vdc.create_gateway(cfg.org.edge_gateway.name,
                                          external_networks=[cfg.system.ext_network.name, cfg.org.mng_nw],
                                          gateway_backing_config=GatewayBackingConfigType.XLARGE.value,
                                          is_default_gateway=True,
                                          selected_extnw_for_default_gw=cfg.system.ext_network.name,
                                          default_gateway_ip=cfg.system.ext_network.gateway,
                                          is_ha_enabled=True,
                                          should_create_as_advanced=True,
                                          is_dr_enabled=True)

    handle_task(client, network_resource.Tasks.Task[0])


# Final report ------------------------------------------------------------------------------------
new_edge_gateway = vdc.get_gateway(cfg.org.edge_gateway.name)
print('\nNew Edge gateway is created -------------------------------------------------')
print('name: {}'.format(new_edge_gateway.attrib['name']))
print('href: {}'.format(new_edge_gateway.attrib['href']))




