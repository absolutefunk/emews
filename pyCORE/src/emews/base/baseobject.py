'''
BaseObject: the base of everything (well, almost...)
This class implements stuff that is common to almost everything class in emews: logging,
configuration, et al.

Created on Apr 9, 2018

@author: Brian Ricks
'''
import logging

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

class BaseObject(object):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        config is the Config required, which contains the logger and configuration
        (system configuration, object configuration...)
        '''
        self._config = config
        # base logger is instantiated in the config object
        self._logger = ThreadLoggerAdapter(self.config.logger, self._config.context_name)

    @property
    def logger(self):
        '''
        returns the logger object
        '''
        return self._logger

    @property
    def config(self):
        '''
        returns the configuration object
        '''
        return self._config

    def context_name(self, context):
        '''
        Updates the context name of the object.  Usually refers to name of active thread in which
        this object belongs.
        '''
        self._config = self._config.clone_with_context(context)
