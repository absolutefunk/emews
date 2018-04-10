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
    __current_object_id = 0  # each object has a unique id assigned

    def __init__(self, config):
        '''
        config is the Config required, which contains the logger and configuration
        (system configuration, object configuration...)
        '''
        self._name = self.__class__.__name__ + "-%d" % BaseObject.__current_thread_id
        BaseObject.__current_thread_id += 1
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

    @property
    def name(self):
        '''
        returns a given name for the object
        '''
        return self._name
