import yaml
from collections import namedtuple

# Load the YAML configuration and convert to an object with properties for top-level entries.
# Values must be dictionaries.
class Config:
    @classmethod
    def load(self, data='config.yml'):
        """Load YAML document"""

        def convert_to_namedtuple(d):
            """Convert a dict into a namedtuple"""
            if not isinstance(d, dict):
                raise ValueError("Can only convert dicts into namedtuple")
            for k, v in d.items():
                if isinstance(v, dict):
                    d[k] = convert_to_namedtuple(v)
            return namedtuple('ConfigDict', d.keys())(**d)

        with open(data, 'r') as f:
            yamlcfg = yaml.load(f)

        return convert_to_namedtuple(yamlcfg)


# Load the implicit config file
cfg = Config.load()

# Load a specific config file
# cfg = Config.load(data='config.yml')

# Print a few input variables to see the variables passed in
print(cfg.connection.verify)
print(cfg.system.ext_network.name)
print(cfg.system.ext_network.portgroup)