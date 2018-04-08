'''
Interface for threads.
Extended by BaseThread and ThreadDecorator.

Created on Apr 8, 2018

@author: Brian Ricks
'''
from abc import ABCMeta, abstractmethod, abstractproperty

class IThread(object):
    '''
    classdocs
    '''
    __metaclass__ = ABCMeta

    @abstractproperty
    def config(self):
        '''
        returns the system config object
        '''
        pass

    @abstractproperty
    def logger(self):
        '''
        returns the logger
        '''
        pass

    @abstractmethod
    def run_thread(self):
        '''
        Executed by the run() method, and for child classes provides the entry point for thread
        execution.  Must be overridden.
        '''
        pass

    @abstractmethod
    def stop(self):
        '''
        Providing appropriate signalling to gracefully shutdown a thread.  Must be overridden.
        '''
        pass
