'''
Interface for classes that wanna be runnable through the ThreadWrapper.
Even though Python is duck typed, and this interface really doesn't do much in practice, it helps
during coding to make sure that the programmer (me) is aware if they (me) forget to implement a
method as part of this contract.

Created on Apr 11, 2018

@author: Brian Ricks
'''
from abc import ABCMeta, abstractmethod

class IRunnable(object):
    '''
    classdocs
    '''
    __metaclass__ = ABCMeta

    @abstractmethod
    def stop(self):
        '''
        Called to signal that the implementing class needs to gracefully exit all tasks.
        '''
        pass

    @abstractmethod
    def start(self):
        '''
        Called by ThreadWrapper as the target.
        '''
        pass
