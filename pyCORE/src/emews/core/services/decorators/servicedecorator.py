'''
Base class for pyCORE service decorators.
Subclasses when overriding the required methods can use super(cls, self) to access the methods
being overridden.

Created on Mar 30, 2018

@author: Brian Ricks
'''
import emews.core.services.iservice

class ServiceDecorator(emews.core.services.iservice.IService):
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

    @property
    def interrupted(self):
        '''
        Returns true if the service has been interrupted (requested to stop).  Use implementaton
        from recipient_service.
        '''
        return self._recipient_service.interrupted

    def sleep(self, time):
        '''
        @Override calls the sleep implementaton of recipient_service.
        '''
        self._recipient_service.sleep(time)

    def start(self):
        '''
        @Override Starts the service.
        '''
        self._recipient_service.start()

    def stop(self):
        '''
        @Override Gracefully exit service
        '''
        self._recipient_service.stop()
