'''
Base class for emews thread decorators.

Created on Apr 8, 2018

@author: Brian Ricks
'''
import emews.base.ithread

class ThreadDecorator(emews.base.ithread.IThread):
    '''
    classdocs
    '''
    def __init__(self, recipient_thread):
        '''
        Constructor
        '''
        self._recipient_thread = recipient_thread

        self.logger.info("Added decorator '%s' to %s.", self.__class__.__name__,
                         recipient_thread.name)

    @property
    def config(self):
        '''
        @Override returns the system config object
        '''
        return self._recipient_thread.config

    @property
    def logger(self):
        '''
        @Override returns the logger
        '''
        return self._recipient_thread.logger

    def run_thread(self):
        '''
        Executed by the run() method, and for child classes provides the entry point for thread
        execution.
        '''
        self._recipient_thread.run_thread()

    def stop(self):
        '''
        Providing appropriate signalling to gracefully shutdown a thread.
        '''
        self._recipient_thread.stop()
