'''
Configuration class.
Encapsulates the system configuration, along with a component (such as a service) configuration.
Allows cloning with a new component config and the shared system config.

Created on Apr 3, 2018

@author: Brian Ricks
'''
import copy
import logging.config
import os

from ruamel.yaml import YAML

import emews.base.configcomponent

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

def prepend_path(filename):
    '''
    Prepends an absolute path to the filename, relative to the directory this
    module was loaded from.
    '''
    path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    return os.path.join(path, filename)

class Config(object):
    '''
    classdocs
    '''
    def __init__(self, nodename, sys_config_path):
        '''
        Constructor
        '''
        self._nodename = nodename

        self._sys_config = emews.base.configcomponent.ConfigComponent(
            parse(prepend_path(sys_config_path)))

        #configure logging
        logging.config.dictConfig(self._sys_config.get('logging', 'log_conf'))

        self._component_config = emews.base.configcomponent.ConfigComponent(None)

    @property
    def nodename(self):
        '''
        returns the nodename of this emews instance
        '''
        return self._nodename

    @property
    def component_config(self):
        '''
        returns the component config object
        '''
        return self._component_config

    def clone_with_new(self, component_config_path):
        '''
        Creates a new Config object with the given component configuration path and shared system
        configuration.
        Note, pylint flags the line where we assign directly to the protected member
        self._component_config.  This is okay in our case as the class is the same for both
        cloned_config and self, so we comment out the warning locally.
        '''
        cloned_config = copy.copy(self)  # shallow copy
        cloned_config._component_config = emews.base.configcomponent.ConfigComponent(  # pylint: disable=W0212
            parse(prepend_path(component_config_path)))

        return cloned_config

    def clone_with_config(self, component_config):
        '''
        Creates a new Config object with the given ConfigComponent object and shared system
        configuration.
        Note, pylint flags the line where we assign directly to the protected member
        self._component_config.  This is okay in our case as the class is the same for both
        cloned_config and self, so we comment out the warning locally.
        '''
        cloned_config = copy.copy(self)  # shallow copy
        cloned_config._component_config = component_config  # pylint: disable=W0212
        return cloned_config

    def clone_with_dict(self, component_dict):
        '''
        Creates a new Config object with the given dictionary and shared system
        configuration.
        Note, pylint flags the line where we assign directly to the protected member
        self._component_config.  This is okay in our case as the class is the same for both
        cloned_config and self, so we comment out the warning locally.
        '''
        cloned_config = copy.copy(self)  # shallow copy
        cloned_config._component_config = emews.base.configcomponent.ConfigComponent(  # pylint: disable=W0212
            component_dict)
        return cloned_config

    def extract_with_key(self, *keys):
        '''
        Creates a new ConfigComponent object using the key as the root for the new object.
        The returned object shares its k/v's with the original dict from this object.
        '''
        return emews.base.configcomponent.ConfigComponent(self._component_config.get(*keys))

    def get(self, *keys):
        '''
        returns a value given the keys from the component config
        '''
        return self._component_config.get(*keys)

    def get_sys(self, *keys):
        '''
        returns a value given the keys from the system config
        '''
        return self._sys_config.get(*keys)
