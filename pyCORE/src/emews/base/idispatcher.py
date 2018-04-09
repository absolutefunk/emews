'''
Part of Dispatcher/Listener functionality (observable/observer).
Interface for Dispatchers.  A Dispatcher dispatches an events to all Listeners subscribed to it.

Created on Apr 8, 2018

@author: Brian Ricks
'''
from abc import ABCMeta, abstractmethod

class IDispatcher(object):
    '''
    classdocs
    '''
    __metaclass__ = ABCMeta

    @abstractmethod
    def dispatch_event(self, dispatched_event):
        '''
        Dispatches dispatched_event to all its Listeners.
        '''
        pass
