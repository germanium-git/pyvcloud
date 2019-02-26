"""
tested with pyvcloud 20.0.2
There are some updated on https://github.com/vmware/pyvcloud/blob/master/pyvcloud/vcd/vdc.py

    the parameter network_cidr replaces gateway and netmask
    def create_isolated_vdc_network(self,
                                    network_name,
                                    network_cidr,
                                    description=None,
                                    primary_dns_ip=None,
                                    secondary_dns_ip=None,
                                    dns_suffix=None,
                                    ip_range_start=None,
                                    ip_range_end=None,
                                    is_dhcp_enabled=None,
                                    default_lease_time=None,
                                    max_lease_time=None,
                                    dhcp_ip_range_start=None,
                                    dhcp_ip_range_end=None,
                                    is_shared=None):
Example:
Logging in...
Fetching org...
Org already exists: HOL
Fetching VDC...
VDC already exists: hol-all-hosts-vxlan
Fetching Network...
Network PY-11.22.33.0m24 does not exist, creating
networkCreateOrgVdcNetwork: Creating Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: queued
networkCreateOrgVdcNetwork: Creating Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: running
networkCreateOrgVdcNetwork: Creating Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: running
networkCreateOrgVdcNetwork: Creating Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: running
networkCreateOrgVdcNetwork: Creating Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: running
networkCreateOrgVdcNetwork: Creating Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: running
networkCreateOrgVdcNetwork: Creating Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: running
networkCreateOrgVdcNetwork: Creating Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: running
networkCreateOrgVdcNetwork: Creating Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: running
networkCreateOrgVdcNetwork: Creating Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: running
networkCreateOrgVdcNetwork: Creating Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: running
networkCreateOrgVdcNetwork: Created Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), status: success
task: 1b6a7d07-fc9b-42ae-b6b2-86eccda4b6f1, Created Network PY-11.22.33.0m24(0d634b2e-455e-46fc-a5d6-3ba1a586e635), result: success

New Isolated network is created -------------------------------------------------
name: PY-11.22.33.0m24
href: https://10.33.95.223/api/admin/network/0d634b2e-455e-46fc-a5d6-3ba1a586e635

Process finished with exit code 0

TODO DHCP service can't be disabled when new network is being deployed

"""

import requests
import sys

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
                                                       gateway_ip=cfg.org.org_isol_nw.gateway,
                                                       netmask=cfg.org.org_isol_nw.netmask,
                                                       ip_range_start=cfg.org.org_isol_nw.ip_range_start,
                                                       ip_range_end=cfg.org.org_isol_nw.ip_range_end,
                                                       is_dhcp_enabled=cfg.org.org_isol_nw.is_dhcp_enabled,
                                                       is_shared=cfg.org.org_isol_nw.is_shared)

    handle_task(client, network_resource.Tasks.Task[0])


# Final report ------------------------------------------------------------------------------------
new_isolated_network = vdc.get_isolated_orgvdc_network(cfg.org.org_isol_nw.name)
print('\nNew Isolated network is created -------------------------------------------------')
print('name: {}'.format(new_isolated_network.attrib['name']))
print('href: {}'.format(new_isolated_network.attrib['href']))
