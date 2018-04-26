'''
Interface for classes that are used as handlers for listeners.

Created on Apr 23, 2018
@author: Brian Ricks
'''
from abc import ABCMeta, abstractmethod

class IHandlerListener(object):
    '''
    classdocs
    '''
    __metaclass__ = ABCMeta

    @abstractmethod
    def handle_accepted_connection(self, sock):
        '''
        Given a socket, perform any initial handling.
        '''
        pass

    @abstractmethod
    def handle_readable_socket(self, sock):
        '''
        Given a socket, read its contents.
        '''
        pass
