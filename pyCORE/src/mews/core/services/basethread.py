'''
Base class for service threads.
Provides extended support for autologging thread info on start.

Created on Mar 26, 2018

@author: Brian Ricks
'''
from abc import abstractmethod

import logging
import threading

def thread_names_str():
    '''
    Concatenates active thread names to a space delim string.
    '''
    thread_names = []
    for thread in threading.enumerate():
        thread_names.append(thread.name)

    return " ".join(thread_names)

class BaseThread(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self, logbase, thr_name):
        '''
        Constructor
        '''
        threading.Thread.__init__(self, name=thr_name)

        self._logger = logging.getLogger(logbase)

    def run(self):
        '''
        @Override of run() from threading.Thread.  Used for logging, and calls
        an additional method which is supposed to be overridden
        '''
        self._logger.debug("(thread started: %s).  %d threads currently alive: [%s]",
                           self.name, threading.active_count(), thread_names_str())

        self.run_service()

        self._logger.debug("(thread terminating: %s).", self.name)

    @abstractmethod
    def run_service(self):
        '''
        Equivalent of the run() method for child classes.  Must be overridden.
        '''
        raise NotImplementedError("Must implement in subclass.")
