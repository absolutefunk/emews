'''
Configuration.
Provides helper functions and a class for storing configuration options.

Created on Apr 3, 2018

@author: Brian Ricks
'''
import copy
import os

from ruamel.yaml import YAML

from emews.base.exceptions import KeychainException, MissingConfigException

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

def keychain_str(target_key, *keys):
    '''
    returns the keychain string
    '''
    key_chain = []
    for key in keys:
        key_chain.append(key)
        if key is target_key:
            break

    return "-->".join(key_chain)

def _get_from_dict(self, config_dict, *keys):
    '''
    Returns a value from the dictionary 'config_dict'.
    '''
    config = config_dict
    for key in keys:
        try:
            config = config.get(key)
        except AttributeError:
            # Implies that 'config' is actually a value.  This should be thrown in the case that
            # 'get' is not an implemented method.  It may be easier to simply check the instance
            # as a dict instead of doing it the duck typing way, but we cannot guarantee what the
            # actual instance is.  However, we do enforce that whatever the type is, it has to at
            # least have a 'get' method.
            raise KeychainException(
                "Keychain '%s': Current value is not a gettable type (cannot get key '%s')."
                % (keychain_str(key, *keys), key))

        if config is None:
            # key doesn't exist at current level in dict
            raise KeychainException(
                "Keychain '%s': key '%s' not present in config (key doesn't exist)."
                % (keychain_str(key, *keys), key))

    return config

class Config(object):
    '''
    classdocs
    '''
    def __init__(self, config, system_options):
        '''
        config parameter passed is a dictionary containing config info
        system_options parameter is a dictionary containing specific system options
        '''
        if config is None:
            raise MissingConfigException("Config dictionary passed cannot be None.")

        self._config = config
        self._user_config = config['config']
        self._node_name = system_options['node_name']
        self._logger = system_options['logger']

    @property
    def node_name(self):
        '''
        Returns the node name.
        '''
        return self._node_name

    @property
    def logger(self):
        '''
        Returns the system logger.
        '''
        return self._logger

    def clone(self, config_dict):
        '''
        Clones the config object using a new config dictionary.  Note that system_options are
        not cloned.
        '''
        new_config = copy.copy(self)
        # Even though we are accessing 'protected' members here, this should be okay as we are
        # doing it from the same class definition.  Disabling pylint here so it won't complain.
        new_config._config = config_dict  # pylint: disable=W0212
        new_config._user_config = config_dict['config']  # pylint: disable=W0212

        return new_config

    def get(self, *keys):
        '''
        Returns a value from the config (under section 'config').
        '''
        return _get_from_dict(self._user_config, keys)

    def get_base(self, *keys):
        '''
        Returns a value from the base config dictionary.  Should not be called unless keys outside
        the 'config' section need to be accessed.
        '''
        return _get_from_dict(self._config, keys)

    def __contains__(self, key):
        '''
        membership test
        '''
        return key in self._user_config
