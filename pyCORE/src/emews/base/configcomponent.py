'''
Individual component configuration.

Created on Mar 30, 2018
@author: Brian Ricks
'''

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
        if self._config is None:
            return None

        config = self._config
        for key in keys:
            config = config.get(key)

        return config

    def __contains__(self, key):
        '''
        membership test
        '''
        return key in self._config
