'''
Interface for pyCORE configuration.
This is used by the main pyCORE configuration class, along with pyCORE service configuration, which
are implemented as decorators.

Created on Mar 30, 2018

@author: Brian Ricks
'''
from abc import ABCMeta, abstractmethod, abstractproperty

class IConfig(object):
    '''
    classdocs
    '''
    __metaclass__ = ABCMeta

    @abstractproperty
    def logbase(self):
        '''
        returns the string representing the pyCORE base logger
        '''
        pass

    @abstractproperty
    def nodename(self):
        '''
        returns the node name assigned
        '''
        pass

    @abstractmethod
    def get(self, key, section=None):
        '''
        Returns a value from the pyCORE conf space.  If a section is given, then from a service
        space.
        '''
        pass
