'''
Base class for emews service decorators.
Subclasses when overriding the required methods can use super(cls, self) to access the methods
being overridden.

Created on Mar 30, 2018
@author: Brian Ricks
'''
import emews.services.iservice

class ServiceDecorator(emews.services.iservice.IService):
    '''
    classdocs
    '''
    def __init__(self, recipient_service):
        '''
        Constructor
        '''
        self._recipient_service = recipient_service
        # cache a reference to the decorator config, if it exists.
        decorator_configcomponent = self._recipient_service.base_config.extract_with_key(
            'decorators', self.__class__.__name__)
        if decorator_configcomponent is not None:
            self._decorator_config = self._recipient_service.base_config.clone_with_config(
                decorator_configcomponent)
        else:
            self._decorator_config = None

        # instantiate any dependencies
        if self._decorator_config is not None and \
                'dependencies' in self._decorator_config.component_config:
            self._dependencies = self._recipient_service.instantiate_dependencies(
                self._decorator_config.get('dependencies'))
        else:
            self._dependencies = None

    @property
    def config(self):
        '''
        @Override Returns the decorator specific config options, if exists.
        Convenience property as the config options exist in the service config and can be
        obtained from self.config.
        '''
        return self._decorator_config

    @property
    def logger(self):
        '''
        @Override Returns the logger object used with the recipient_service.
        '''
        return self._recipient_service.logger

    @property
    def service_config(self):
        '''
        Returns the recipient_service config.  Convenience property.
        '''
        return self._recipient_service.config

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
