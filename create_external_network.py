import yaml
from collections import namedtuple
import requests

from pyvcloud.vcd.client import BasicLoginCredentials
from pyvcloud.vcd.client import Client
from pyvcloud.vcd.platform import Platform


# Load the YAML configuration and convert to an object with properties for top-level entries.
# Values must be dictionaries.
class Config:
    @classmethod
    def load(self, data='config_nogit.yml'):
        """Load YAML document"""

        def convert_to_namedtuple(d):
            """Convert a dict into a namedtuple"""
            if not isinstance(d, dict):
                raise ValueError("Can only convert dicts into namedtuple")
            for k,v in d.items():
                if isinstance(v, dict):
                    d[k] = convert_to_namedtuple(v)
            return namedtuple('ConfigDict', d.keys())(**d)

        with open(data, 'r') as f:
            yamlcfg = yaml.load(f)

        return convert_to_namedtuple(yamlcfg)


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
print("Fetching External Network...")
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


# Final report ------------------------------------------------------------------------------------
new_external_network = platform.get_external_network(cfg.system.ext_network.name)
print('\nNew External network is created -------------------------------------------------')
print('name: {}'.format(new_external_network.attrib['name']))
print('href: {}'.format(new_external_network.attrib['href']))
