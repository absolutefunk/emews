'''
Configuration.
Provides helper functions for parsing configuration options, and system-wide properties.

Created on Apr 3, 2018

@author: Brian Ricks
'''
from ruamel.yaml import YAML

def parse(filename):
    '''
    Parses the given filename (if it exists), and returns a dictionary.
    '''
    if filename is None:
        return None

    f = open(filename)

    yaml = YAML()
    dct = yaml.load(f)

    return dct

'''
Dictionary that contains the system-wide properties.  One of these is the logger, which is also
designed to be module-level.  The main reason we don't directly grab the logger from the logger
module is that we use a LoggerAdapter to insert the node name, which itself would need to be
available.
'''
_system_properties = dict()

def set_system_properties(system_properties):
    '''
    Sets the system-wide properties.  Objects such as BaseObject pull important properties from this
    '''
    _system_properties.update(system_properties)

def get_system_property(key):
    '''
    Returns the system property based on the input key
    '''
    return _system_properties[key]
