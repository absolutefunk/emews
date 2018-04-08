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
                         recipient_thread.__class__.__name__)
