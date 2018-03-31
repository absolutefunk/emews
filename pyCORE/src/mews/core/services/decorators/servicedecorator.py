'''
Base class for pyCORE service decorators.
Subclasses when overriding the require methods can use super(cls, self) to access the methods
being overridden.

Created on Mar 30, 2018

@author: Brian Ricks
'''
import mews.core.services.iservice

class ServiceDecorator(mews.core.services.iservice.IService):
    '''
    classdocs
    '''
    def __init__(self, recipient_service):
        '''
        Constructor
        '''
        self._recipient_service = recipient_service
        self.logger.info("Added decorator '%s' to %s.", self.__class__.__name__,
                         recipient_service.name)

    @property
    def config(self):
        '''
        @Override Returns the service config object.
        '''
        return self._recipient_service.config

    @property
    def logger(self):
        '''
        @Override Returns the logger object used with the recipient_service.
        '''
        return self._recipient_service.logger

    def start(self):
        '''
        @Override Starts the service.
        '''
        return self._recipient_service.start()

    def stop(self):
        '''
        @Override Gracefully exit service
        '''
        return self._recipient_service.stop()
