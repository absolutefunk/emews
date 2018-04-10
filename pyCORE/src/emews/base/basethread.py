'''
Base class for threads.
Provides extended support for autologging thread info on start.

Created on Mar 26, 2018

@author: Brian Ricks
'''
from abc import abstractmethod
import logging
import threading

import emews.base.baseobject

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

class BaseThread(emews.base.baseobject.BaseObject):
    '''
    classdocs
    '''

    def __init__(self, config):
        '''
        Constructor
        '''
        super(BaseThread, self).__init__(config, self._thread_name)

        # Override logger from BaseObject
        self._logger = ThreadLoggerAdapter(self.config.logger, self._thread_name)

    def run_thread(self):
        '''
        @Override of run() from threading.Thread.  Used for logging, and calls
        an additional method which is supposed to be overridden
        '''
        self.logger.info("Thread started.")

        self.run()

        self.logger.info("Thread terminating.")

    @abstractmethod
    def run(self):
        '''
        Executed by the run() method, and for child classes provides the entry point for thread
        execution.  Must be overridden.
        '''
        pass
