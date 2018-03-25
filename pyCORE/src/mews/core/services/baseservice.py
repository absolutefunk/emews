'''
Base class for pyCORE services

Created on Mar 5, 2018

@author: Brian Ricks
'''

from abc import abstractmethod

class BaseService(object):
    '''
    classdocs
    '''

    @abstractmethod
    def configure(self, config_file=None):
        '''
        Configures the service.
        Must be implemented in child class
        '''
        raise NotImplementedError("Must implement in subclass.")

    @abstractmethod
    def needs_config(self):
        '''
        Returns true if a config file is needed for the service.
        Must be implemented in child class
        '''
        raise NotImplementedError("Must implement in subclass.")

    @abstractmethod
    def start(self):
        '''
        Starts the service.
        Must be implemented in child class
        '''
        raise NotImplementedError("Must implement in subclass.")

    @abstractmethod
    def stop(self):
        '''
        Stops the service.
        Must be implemented in child class
        '''
        raise NotImplementedError("Must implement in subclass.")
