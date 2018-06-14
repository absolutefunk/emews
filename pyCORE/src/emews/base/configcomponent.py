'''
Individual component configuration.

Created on Mar 30, 2018
@author: Brian Ricks
'''
import copy
import numbers

from emews.base.exceptions import KeychainException, MissingConfigException

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

def get_from_dict(self, config_dict, *keys):
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

class ConfigComponent(object):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        config parameter passed is a dictionary containing config info
        '''
        if config is None:
            raise MissingConfigException("Dictionary passed cannot be None.")

        self._config = config
        self._user_config = config['config']
        self._system_options = config['system_options']

    @property
    def system(self):
        '''
        Returns the system options.
        '''
        return self._system_options

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
        return get_from_dict(self._user_config, keys)

    def get_base(self, *keys):
        '''
        Returns a value from the base config dictionary.  Should not be called unless keys outside
        the 'config' section need to be accessed.
        '''
        return get_from_dict(self._config, keys)

    def __contains__(self, key):
        '''
        membership test
        '''
        return key in self._user_config
