'''
BaseObject: the base of everything (well, almost...)
This class implements stuff that is common to almost everything class in emews: logging,
configuration, et al.

Created on Apr 9, 2018

@author: Brian Ricks
'''

class BaseObject(object):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        config is the Config required, which contains the logger and configuration
        (system configuration, object configuration...)
        '''
        self._config = config
        self._logger = self._config.logger  # logger is a property of Configuration

    @property
    def logger(self):
        '''
        returns the logger object
        '''
        return self._logger

    @property
    def config(self):
        '''
        returns the configuration object
        '''
        return self._config
