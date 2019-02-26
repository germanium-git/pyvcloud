import yaml
from collections import namedtuple


# Load the YAML configuration and convert to an object with properties for top-level entries.
# Values must be dictionaries.
class Config:
    @classmethod
    def load(self, data):
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