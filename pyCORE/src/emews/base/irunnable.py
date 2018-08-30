'''
Interface for classes that wanna be runnable through the ThreadWrapper.
Even though Python is duck typed, and this interface really doesn't do much in practice, it helps
during coding to make sure that the programmer (me) is aware if they (me) forget to implement a
method as part of this contract.

Created on Apr 11, 2018
@author: Brian Ricks
'''
import abc

# Python 2.7 does not contain __slots__ in the ABCMeta class definition, which we need.
ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})

class IRunnable(ABC):
    '''
    classdocs
    '''
    __slots__ = ()

    @abc.abstractmethod
    def stop(self):
        '''
        Called to signal that the implementing class needs to gracefully exit all tasks.
        '''
        pass

    @abc.abstractmethod
    def start(self):
        '''
        Called to start execution of implementing task.
        '''
        pass
