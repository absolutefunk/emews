'''
Individual component configuration.

Created on Mar 30, 2018
@author: Brian Ricks
'''
import numbers

def keychain_str(target_key, *keys):
    '''
    returns the keychain string
    '''
    key_chain = []
    for key in keys:
        if key is target_key:
            key_chain.append(key)
            break
        key_chain.append(key)

    return "-->".join(key_chain)


class ConfigComponent(object):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        config parameter passed is a dictionary containing config info
        '''
        self._config = config

    def get(self, *keys):
        '''
        Returns a value from the config dictionay.
        '''
        config = self._config
        for key in keys:
            if config is None or isinstance(config, (basestring, numbers.Number)):
                # Implies that 'config is actually a value (we use ValueError instead of KeyError
                # due to KeyError quoting the message, and also to consolidate this with ValueError
                # exceptions often raised when checking parameters originating from here).
                raise ValueError(
                    "keychain '%s': reached value '%s' before using key '%s' (key doesn't exist)."
                    % (keychain_str(key, *keys), config, key))

            config = config[key]

        return config

    def __contains__(self, key):
        '''
        membership test
        '''
        return key in self._config
