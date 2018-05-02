'''
Interface for classes that perform net stuff (clients, listeners)

Created on Apr 26, 2018
@author: Brian Ricks
'''
from abc import ABCMeta, abstractmethod, abstractproperty

class INet(object):
    '''
    classdocs
    '''
    __metaclass__ = ABCMeta

    @abstractproperty
    def socket(self):
        '''
        Returns a socket (client socket if client, listener socket if listener).
        '''
        pass

    @abstractproperty
    def interrupted(self):
        '''
        returns whether the net-based object has been requested to stop
        '''
        pass

    @abstractmethod
    def request_write(self, sock):
        '''
        This is called when a socket is requested to be written to.
        '''
        pass

    @abstractmethod
    def request_close(self, sock):
        '''
        This is called when a socket needs to be closed.
        '''
        pass

    @abstractmethod
    def start(self):
        '''
        Starts the net-based logic.
        '''
        pass

    @abstractmethod
    def stop(self):
        '''
        Stops (gracefully) the net-based logic.
        '''
        pass
