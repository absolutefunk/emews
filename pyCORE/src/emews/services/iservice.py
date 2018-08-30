'''
Interface for emews services.
Concrete class should inherit BaseClass or a subclass of it.  This interface is mainly to properly
support service decorator classes.

Created on Mar 30, 2018

@author: Brian Ricks
'''
import abc

import emews.base.irunnable

class IService(emews.base.irunnable.IRunnable):
    '''
    classdocs
    '''
    __slots__ = ()

    @abc.abstractproperty
    def config(self):
        '''
        Returns the config object.
        '''
        pass

    @abc.abstractproperty
    def helpers(self):
        '''
        Returns the helpers object.
        '''
        pass

    @abc.abstractproperty
    def interrupted(self):
        '''
        Returns true if the service has been interrupted (requested to stop)
        '''
        pass

    @abc.abstractmethod
    def initialize(self, stage):
        '''
        Called after object construction.  Concrete services perform their initialization here.
        stage refers to the current running progress of the eMews system.
        '''
        pass

    @abc.abstractmethod
    def sleep(self, time):
        '''
        Provides an interruptable method for sleeping.
        '''
        pass
