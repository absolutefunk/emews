'''
Base class for emews service decorators.
Subclasses when overriding the required methods can use super(cls, self) to access the methods
being overridden.

Created on Mar 30, 2018
@author: Brian Ricks
'''
import emews.base.baseobject
from emews.base.exceptions import KeychainException
import emews.services.iservice

class ServiceDecorator(emews.base.baseobject.BaseObject, emews.services.iservice.IService):
    '''
    classdocs
    '''
    def __init__(self, recipient_service):
        '''
        Constructor
        '''
        super(ServiceDecorator, self).__init__(recipient_service.config)
        self._recipient_service = recipient_service
        # cache a reference to the decorator config, if it exists.
        try:
            self._decorator_config = self.config.extract_with_key(
                'decorators', self.__class__.__name__)
        except KeychainException:
            self.logger.info("No decorator config found ...")
            self._decorator_config = None

        # instantiate any dependencies (decorator)
        if self._decorator_config is not None and 'dependencies' in self._decorator_config:
            self._dependencies = self.instantiate_dependencies(
                self._decorator_config.get('dependencies'))
        else:
            self._dependencies = None

    @property
    def decorator_config(self):
        '''
        Returns the decorator config section only.  Convenience property.
        '''
        return self._decorator_config

    @property
    def service_config(self):
        '''
        @Override Returns the service config section only.  Convenience property.
        '''
        return self._recipient_service.service_config

    @property
    def dependencies(self):
        '''
        @Override returns the dependencies of this decorator, or None if none are defined
        '''
        return self._dependencies

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
