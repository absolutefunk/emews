'''
Configuration class.
Encapsulates the system configuration, along with a component (such as a service) configuration.
Allows cloning with a new component config and the shared system config.

Created on Apr 3, 2018

@author: Brian Ricks
'''
import copy
import logging
import os

from ruamel.yaml import YAML

import emews.core.configcomponent

def parse(filename):
    '''
    Parses the given filename (if it exists), and returns a dictionary.
    '''
    if filename is None:
        return None

    yaml = YAML()
    dct = yaml.load(filename)

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
        self._sys_config = emews.core.configcomponent.ConfigComponent(
            parse(prepend_path(sys_config_path)))

        self._logger = logging.LoggerAdapter(logging.getLogger(
            self._sys_config.get('logging', 'base_logger')), {'nodename': self._nodename})

        self._component_config = None

    @property
    def nodename(self):
        '''
        returns the nodename of this emews instance
        '''
        return self._nodename

    @property
    def logger(self):
        '''
        returns the main logger object
        '''
        return self._logger

    @property
    def component_config(self):
        '''
        returns the component config object
        '''
        return self._component_config

    def clone_with_new(self, component_config_path):
        '''
        Creates a new Config object with the given component configuration and shared system
        configuration.
        Note, pylint flags the line where we assign directly to the protected member
        self._component_config.  This is okay in our case as the class is the same for both
        cloned_config and self, so we comment out the warning locally.
        '''
        cloned_config = copy.copy(self)
        cloned_config._component_config = emews.core.configcomponent.ConfigComponent(  # pylint: disable=W0212
            parse(prepend_path(component_config_path)))

        return cloned_config

    def extract_with_key(self, *keys):
        '''
        Creates a new ConfigComponent object using the key as the root for the new object.
        The returned object shares its k/v's with the original dict from this object.
        '''
        if self._component_config is None:
            return None

        try:
            extracted_dct = self._component_config.get(keys)
        except KeyError:
            return None

        return emews.core.configcomponent.ConfigComponent(extracted_dct)

    def get(self, *keys):
        '''
        returns a value given the keys from the component config
        '''
        return self._component_config.get(keys)

    def get_sys(self, *keys):
        '''
        returns a value given the keys from the system config
        '''
        return self._sys_config.get(keys)
