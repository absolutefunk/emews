'''
Individual component configuration.

Created on Mar 30, 2018
@author: Brian Ricks
'''
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

    def get(self, *keys):
        '''
        Returns a value from the config dictionay.
        '''
        if self._config is None:
            # nothing to get
            raise KeychainException(
                "Keychain '%s': config dictionary is empty." % keychain_str(None, *keys))

        config = self._config
        for key in keys:
            if isinstance(config, (basestring, numbers.Number, bool)):
                # Implies that 'config is actually a value.
                raise KeychainException(
                    "Keychain '%s': reached value '%s' before using key '%s' (key doesn't exist)."
                    % (keychain_str(key, *keys), config, key))

            config = config.get(key)

            if config is None:
                # key doesn't exist at current level in dict
                raise KeychainException(
                    "Keychain '%s': key '%s' not present in config (key doesn't exist)."
                    % (keychain_str(key, *keys), key))

        return config

    def __contains__(self, key):
        '''
        membership test
        '''
        return key in self._config
