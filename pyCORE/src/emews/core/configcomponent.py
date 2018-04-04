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
        Constructor
        '''
        self._config = config

    def get(self, *keys):
        '''
        Returns a value from the config dictionay.
        '''
        config = self._config
        for key in keys:
            config = config[key]

        return config
