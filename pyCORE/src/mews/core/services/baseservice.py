'''
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
        configures the service.
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
