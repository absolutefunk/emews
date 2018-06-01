'''
Interface for emews services.
Concrete class should inherit BaseClass or a subclass of it.  This interface is mainly to properly
support service decorator classes.

Created on Mar 30, 2018

@author: Brian Ricks
'''
from abc import ABCMeta, abstractmethod, abstractproperty

import emews.base.irunnable

class IService(emews.base.irunnable.IRunnable):
    '''
    classdocs
    '''
    __metaclass__ = ABCMeta

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
