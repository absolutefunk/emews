'''
Interface for pyCORE services.
Concrete class should inherit BaseClass or a subclass of it.  This interface is mainly to properly
support service decorator classes.

Created on Mar 5, 2018

@author: Brian Ricks
'''
from abc import ABCMeta, abstractmethod, abstractproperty

class IService(object):
    '''
    classdocs
    '''
    __metaclass__ = ABCMeta

    @abstractproperty
    def config(self):
        '''
        Returns the service config object.
        '''
        pass

    @abstractproperty
    def logger(self):
        '''
        Returns the service logger object.
        '''
        pass

    @abstractproperty
    def interrupted(self):
        '''
        Returns true if the service has been interrupted (requested to stop)
        '''
        pass

    @abstractmethod
    def sleep(self, time):
        '''
        Provides an interruptable method for sleeping.
        '''
        pass

    @abstractmethod
    def start(self):
        '''
        Starts the service.
        '''
        pass

    @abstractmethod
    def stop(self):
        '''
        Gracefully exit service.
        '''
        pass
