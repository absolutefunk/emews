'''
Configuration and system properties module.

Created on Apr 3, 2018

@author: Brian Ricks
'''
from ruamel.yaml import YAML

from emews.base.exceptions import KeychainException

'''
Module-level functions related to configuration loading/parsing.
'''
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
BaseConfig and Derived classes are used for eMews services, helpers, and other BaseObject
derived classes outside of the eMews system base.  These classes provide a consistent means of
per-object configuration.
'''
class BaseConfig(object):
    '''
    Base configuration object.
    '''
    def __init__(self, config_dict):
        '''
        Constructor
        '''
        self._dict = config_dict

    def get(self, *keys):
        '''
        Given a keychain, returns a value, or throws a KeychainException if value does not exist
        along the keychain.
        '''
        keychain_str = ""
        first_iter = True
        current_key = {}

        for key in keys:
            if not isinstance(current_key, dict):
                # previous key's value is not a dict (and more keys in the keychain)
                raise KeychainException("Keychain [%s], reached end of chain, but more keys given."\
                    % keychain_str)

            if first_iter:
                keychain_str += key
                first_iter = False
            else:
                keychain_str += " --> " + key

            try:
                current_key = self._dict[key]
            except KeyError:
                # current key is not in the dict
                raise KeychainException("Keychain [%s], key %s not in chain." % keychain_str, key)

        return current_key

class ServiceConfig(BaseConfig):
    '''
    Extension of BaseConfig for eMews Services
    '''
    def __init__(self, config_dict):
        '''
        Constructor
        '''
        super(ServiceConfig, self).__init__(config_dict['config'])
        self._dependencies = BaseConfig(config_dict['dependencies'])

    @property
    def dependencies(self):
        '''
        Returns the dependencies BaseConfig.
        '''
        return self._dependencies

'''
Dictionary that contains the system-wide properties, which allows for these properties to be
available to eMews classes without dependency injection.  While dependency injection is
more straightforward for unit testing, it's nice from a design standpoint to have a common
methodology of access (ie, self.logger), instead of each class pulling it from the passed in local
config and doing whatever with it.

The basic idea is that most eMews classes inherit BaseObject, and that BaseObject pulls the system
properties from the dict to instance variables.
'''
EXPECTED_UPDATES = 1  # number of times set_system_properties() is expected to be called
_system_properties = dict()

def set_system_properties(system_properties):
    '''
    Sets the system-wide properties.  We keep track of how many times the system properties have
    been updated as a way to check for unexpected updates (unintentional updates - intentional
    direct access of dict is beyond our control).
    '''
    if 'update' not in _system_properties:
        _system_properties['update'] = 0

    _system_properties['update'] += 1
    _system_properties.update(system_properties)

def get_system_property(key):
    '''
    Returns the system property based on the input key.  Objects such as BaseObject pull important
    properties from this.
    '''
    return _system_properties[key]
