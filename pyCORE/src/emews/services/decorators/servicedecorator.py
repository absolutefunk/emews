'''
Base class for emews service decorators.
Subclasses when overriding the required methods can use super(cls, self) to access the methods
being overridden.

Created on Mar 30, 2018
@author: Brian Ricks
'''
import emews.base.baseobject
import emews.services.iservice

class ServiceDecorator(emews.base.baseobject.BaseObject, emews.services.iservice.IService):
    '''
    classdocs
    '''
    def __init__(self, config, recipient_service):
        '''
        config: decorator config
        recipient_service: previous decorator in the chain (or service if root of chain)
        '''
        super(ServiceDecorator, self).__init__(config)
        self._recipient_service = recipient_service

    @property
    def interrupted(self):
        '''
        @Override Returns true if the service has been interrupted (requested to stop).
        Use implementaton from recipient_service.
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
