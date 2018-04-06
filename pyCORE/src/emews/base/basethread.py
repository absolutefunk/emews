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
    Updates the thread name from the default one (<main>) to the name of this thread.
    '''
    def __init__(self, logger_instance, thr_name, extra=None):
        '''
        Constructor
        '''
        super(ThreadLoggerAdapter, self).__init__(logger_instance, extra)
        self._logkw_thread_name = thr_name

    def process(self, msg, kwargs):
        '''
        @Override of logging.LoggerAdapter process() method.
        Replaces the value of 'threadname' with the name of thread passed (in 'extra').
        '''
        if 'threadname' in kwargs:
            kwargs['threadname'] = self._logkw_thread_name

        return msg, kwargs

class BaseThread(threading.Thread):
    '''
    classdocs
    '''
    __current_thread_id = 0  # each thread has a unique id assigned

    def __init__(self, sys_config, thr_name):
        '''
        Constructor
        '''
        self._thread_name = thr_name+"-%d" % BaseThread.__current_thread_id

        super(BaseThread, self).__init__(name=self._thread_name)

        BaseThread.__current_thread_id += 1
        self._sys_config = sys_config
        self._logger = ThreadLoggerAdapter(self._sys_config.logger, self._thread_name)

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
        pass

    @abstractmethod
    def stop(self):
        '''
        Providing appropriate signalling to gracefully shutdown a thread.  Must be overridden.
        '''
        pass
