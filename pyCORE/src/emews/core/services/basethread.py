'''
Base class for threads.
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

    def __init__(self, sys_config, thr_name):
        '''
        Constructor
        '''
        self._thr_name = thr_name+"-%d" % BaseThread.__current_thread_id

        super(BaseThread, self).__init__(self, name=self._thr_name)

        BaseThread.__current_thread_id += 1
        self._sys_config = sys_config
        self._logger = ThreadLoggerAdapter(self._sys_config.logger, {'thr_name': self._thr_name})

    @property
    def config(self):
        '''
        returns the system config object
        '''
        return self._sys_config

    @property
    def logger(self):
        '''
        returns the logger
        '''
        return self._logger

    def run(self):
        '''
        @Override of run() from threading.Thread.  Used for logging, and calls
        an additional method which is supposed to be overridden
        '''
        self._logger.info("Thread started.")

        self.run_thread()

        self._logger.info("Thread terminating.")

    @abstractmethod
    def run_thread(self):
        '''
        Executed by the run() method, and for child classes provides the entry point for thread
        execution.  Must be overridden.
        '''
        raise NotImplementedError("Must implement in subclass.")

    @abstractmethod
    def stop(self):
        '''
        Providing appropriate signalling to gracefully shutdown a thread.  Must be overridden.
        '''
        raise NotImplementedError("Must implement in subclass.")
