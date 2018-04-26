'''
Interface for classes that are used as handlers for net clients.

Created on Apr 26, 2018
@author: Brian Ricks
'''
from abc import ABCMeta, abstractmethod

class IHandlerClient(object):
    '''
    classdocs
    '''
    __metaclass__ = ABCMeta

    @abstractmethod
    def handle_readable_socket(self, sock):
        '''
        Given a socket, read its contents.
        '''
        pass
