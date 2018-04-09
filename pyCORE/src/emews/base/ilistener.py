'''
Part of Dispatcher/Listener functionality (observable/observer).
Interface for Listeners.  A Listener implements a notify_listener method which contains some event
that the Listener uses as context to determine what to do.

Created on Apr 8, 2018

@author: Brian Ricks
'''
from abc import ABCMeta, abstractmethod

class IListener(object):
    '''
    classdocs
    '''
    __metaclass__ = ABCMeta

    @abstractmethod
    def update_listener(self, dispatched_event):
        '''
        Called from a dispatcher when an event is dispatched.   Any listener subscribing to the
        dispatcher will have this method invoked.
        '''
        pass
