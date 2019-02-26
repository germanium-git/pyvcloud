#!/usr/bin/env python3

"""
===================================================================================================
   Author:          Petr Nemec
   Description:     It creates
                    - external network
                    - edge gateway
                    - routed Org VDC network

   Date:            2019-00-26
===================================================================================================
"""

import requests
import sys

from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.org import Org
from pyvcloud.vcd.vdc import VDC
from pyvcloud.vcd.platform import Platform

from pyvcloud.vcd.client import GatewayBackingConfigType

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

# Create an instance of the Class Platform --------------------------------------------------------
platform = Platform(client)

# Ensure External Network doesn't exist -----------------------------------------------------------
print("\nFetching External Network...")
try:
    network_resource = platform.get_external_network(cfg.system.ext_network.name)
    print("External Network already exists: {0}".format(cfg.system.ext_network.name))
except Exception:
    print("External Network {0} does not exist, creating".format(cfg.system.ext_network.name))
    # Ensure Port Group exists.
    print("Fetching Port Groups...")
    # Fetch dvportgroups - not startswith('vxw-')
    records = platform.list_available_port_group_names(vim_server_name=cfg.system.vcenter)
    if cfg.system.ext_network.portgroup in records:
        print("Port Group {0} found".format(cfg.system.ext_network.portgroup))
        print("Creating External Network {0} ".format(cfg.system.ext_network.name))
        network_resource = platform.create_external_network(cfg.system.ext_network.name,
                                                            cfg.system.vcenter,
                                                            [cfg.system.ext_network.portgroup],
                                                            cfg.system.ext_network.gateway,
                                                            cfg.system.ext_network.mask,
                                                            [cfg.system.ext_network.range])

    else:
        print("Port Group {0} does not exist, exiting".format(cfg.system.ext_network.portgroup))


# Status report -----------------------------------------------------------------------------------
new_external_network = platform.get_external_network(cfg.system.ext_network.name)
print('\nNew External network is created -------------------------------------------------')
print('name: {}'.format(new_external_network.attrib['name']))
print('href: {}'.format(new_external_network.attrib['href']))


# Ensure the org exists. --------------------------------------------------------------------------
print("\nFetching org...")
try:
    # This call gets a record that we can turn into an Org class.
    org_record = client.get_org_by_name(cfg.org.name)
    org = Org(client, href=org_record.get('href'))
    print("Org already exists: {0}".format(org.get_name()))
except Exception:
    print("Org does not exist, exiting")
    sys.exit()


# Ensure VDC exists. ------------------------------------------------------------------------------
print("\nFetching VDC...")
try:
    vdc_resource = org.get_vdc(cfg.org.vdc_name)
    vdc = VDC(client, resource=vdc_resource)
    print("VDC already exists: {0}".format(cfg.org.vdc_name))
except Exception:
    print("VDC {0} does not exist, exiting".format(cfg.org['vdc_name']))
    sys.exit()


# Ensure the edge doesn't exist. ------------------------------------------------------------------
print("\nFetching Edges...")
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


# Status report -----------------------------------------------------------------------------------
new_edge_gateway = vdc.get_gateway(cfg.org.edge_gateway.name)
print('\nNew Edge gateway is created -------------------------------------------------')
print('name: {}'.format(new_edge_gateway.attrib['name']))
print('href: {}'.format(new_edge_gateway.attrib['href']))


# Ensure Routed Org Network doesn't exist. --------------------------------------------------------
print("\nFetching Network...")
try:
    network_resource = vdc.get_routed_orgvdc_network(cfg.org.org_routed_nw.name)
    print("Network already exists: {0}".format(cfg.org.org_routed_nw.name))
except Exception:
    print("Network {0} does not exist, creating".format(cfg.org.org_routed_nw.name))
    network_resource = vdc.create_routed_vdc_network(cfg.org.org_routed_nw.name,
                                                     cfg.org.edge_gateway.name,
                                                     cfg.org.org_routed_nw.cidr,
                                                     dns_suffix=cfg.org.org_routed_nw.dns_suffix,
                                                     ip_range_start=cfg.org.org_routed_nw.ip_range_start,
                                                     ip_range_end=cfg.org.org_routed_nw.ip_range_end,
                                                     is_shared=cfg.org.org_routed_nw.is_shared,
                                                     distributed_interface=cfg.org.org_routed_nw.distributed_interface)

    handle_task(client, network_resource.Tasks.Task[0])

# Status report -----------------------------------------------------------------------------------
new_routed_network = vdc.get_routed_orgvdc_network(cfg.org.org_routed_nw.name)
print('\nNew routed network is created -------------------------------------------------')
print('name: {}'.format(new_routed_network.attrib['name']))
print('href: {}'.format(new_routed_network.attrib['href']))
