'''
Base class for service threads.
Provides extended support for autologging thread info on start.

Created on Mar 26, 2018

@author: Brian Ricks
'''
from abc import abstractmethod

import logging
import threading

class ThreadLoggerAdapter(logging.LoggerAdapter):
    '''
    Prepends the thread name to log messages originating from the thread, so the log messages from
    this thread will be easy to identify.
    '''
    def process(self, msg, kwargs):
        '''
        @Override of logging.LoggerAdapter process() method.
        '''
        return '(%s) %s' % (self.extra['thr_name'], msg), kwargs

class BaseThread(threading.Thread):
    '''
    classdocs
    '''
    __current_thread_id = 0  # each thread has a unique id assigned

    def __init__(self, config, thr_name):
        '''
        Constructor
        '''
        self._thr_name = thr_name+"-%d" % BaseThread.__current_thread_id

        threading.Thread.__init__(self, name=self._thr_name)

        BaseThread.__current_thread_id += 1
        self._logger = ThreadLoggerAdapter(logging.getLogger(config.logbase),
                                           {'thr_name': self._thr_name})

    def run(self):
        '''
        @Override of run() from threading.Thread.  Used for logging, and calls
        an additional method which is supposed to be overridden
        '''
        self._logger.info("Thread started.")

        self.run_service()

        self._logger.info("Thread terminating.")

    @abstractmethod
    def run_service(self):
        '''
        Equivalent of the run() method for child classes.  Must be overridden.
        '''
        raise NotImplementedError("Must implement in subclass.")

    @abstractmethod
    def stop(self):
        '''
        Providing appropriate signalling to gracefully shutdown a thread.  Must be overridden.
        '''
        raise NotImplementedError("Must implement in subclass.")
