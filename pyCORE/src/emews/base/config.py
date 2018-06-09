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

import emews.version
import emews.base.configcomponent
from emews.base.exceptions import MissingConfigException

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
    def __init__(self, sys_config_path, node_config_path=None, node_name=None):
        '''
        Constructor
        '''
        sys_config_dict = parse(sys_config_path)
        if node_config_path is not None:
            # parse the per node config
            node_config_dict = parse(node_config_path)
            if not 'general' in node_config_dict:
                print "node_config: key 'general' is missing (section)."
                raise ValueError("node_config: key 'general' is missing (section).")
            if not 'node_name' in node_config_dict['general']:
                print "node_config: key 'general-->node_name' is missing."
                raise ValueError("node_config: key 'general-->node_name' is missing.")

            node_config_key = str(node_config_dict['general']['node_name']) + "_config"
            if node_config_key in sys_config_dict:
                print "system_config: key '%s' is present.  Please delete or rename."
                raise ValueError("system_config: key '%s' is present.  Please delete or rename.")

            sys_config_dict[node_config_key] = node_config_dict

        # set the name of the node running this daemon instance
        if node_name is not None:
            # top precedence: if the node name is manually given
            self._nodename = node_name
        elif node_config_path is not None and 'node_name' in node_config_dict['general']:
            # if the node name is given in the node config (and no node name was passed as arg)
            self._nodename = node_config_dict['general']['node_name']
        else:
            # no node name is given anywhere, use the name of the host
            self._nodename = socket.gethostname()

        self._project_root = os.path.dirname(emews.version.__file__)
        self._sys_config = emews.base.configcomponent.ConfigComponent(sys_config_dict)

        #configure logging
        logging.config.dictConfig(self._sys_config.get('logging', 'log_conf'))

        self._component_config = None

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

    @property
    def root_path(self):
        '''
        returns the root path (where __main__ is located)
        '''
        return self._project_root

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
        if component_dict is None:
            raise MissingConfigException("clone_with_dict cannot be used with NoneType.")

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

    def get_new(self, *keys):
        '''
        returns a new Config object with the component config created from the keys
        '''
        if len(keys) == 1 and keys[0] is None:
            return self.clone_with_config(None)

        return self.clone_with_dict(self.get(*keys))

    def get_sys_new(self, *keys):
        '''
        Returns a new Config object with the component config created from the keys, and the dict
        used to create the component config extracted from the system config.
        '''
        return self.clone_with_dict(self.get_sys(*keys))

    def get(self, *keys):
        '''
        returns a value given the keys from the component config
        '''
        if self._component_config is None:
            raise MissingConfigException("No component configuration present.  "\
                "Does this component require configuration options?")
        return self._component_config.get(*keys)

    def get_sys(self, *keys):
        '''
        returns a value given the keys from the system config
        '''
        return self._sys_config.get(*keys)
