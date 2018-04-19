'''
Base class for pyCORE services.
While this class is abstract, it still inherits the IService interface.  This is mainly to
separate base service functionality from the service decorators, which would be redundant otherwise.
Also instantiating decorators would be awkward if the base decorator had to call the BaseService
contructor.

Services must be in their own module, with the service name the same as the module name (service
name can use upper camelCase - ServiceName for example).  This is so the string name passed to
build the appropriate service can also perform module lookup.

Created on Mar 5, 2018

@author: Brian Ricks
'''

from abc import abstractmethod
from threading import Event

import emews.base.baseobject
import emews.base.config
import emews.services.iservice

class BaseService(emews.base.baseobject.BaseObject, emews.services.iservice.IService):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(BaseService, self).__init__(config)
        self._service_interrupt_event = Event()  # used to interrupt Event.wait() on stop()
        self._interrupted = False  # set to true on stop()

        # instantiate any dependencies
        if self.base_config.component_config is not None:
            self._service_config = self.base_config.extract_with_key('config')
            if 'dependencies' in self.base_config.component_config:
                self._dependencies = self.instantiate_dependencies(
                    self.base_config.get('dependencies'))
            else:
                self._dependencies = None
        else:
            self._service_config = None

    @property
    def config(self):
        '''
        @Override Returns the service key of the config as a ConfigComponent.
        '''
        return self._service_config

    @property
    def base_config(self):
        '''
        returns the entire config
        '''
        return super(BaseService, self).config

    @property
    def dependencies(self):
        '''
        @Override returns the dependencies of this decorator, or None if none are defined
        '''
        return self._dependencies

    @property
    def interrupted(self):
        '''
        Returns true if the service has been interrupted (requested to stop).  Uses events.
        '''
        return self._interrupted

    def sleep(self, time):
        '''
        @Override Wraps the event.wait().  Convenience method.
        '''
        self.logger.debug("Sleeping for %s seconds.", time)
        self._service_interrupt_event.wait(time)

    @abstractmethod
    def run_service(self):
        '''
        Where the service entrance code goes.  Must be implemented by child class.
        '''
        pass

    def start(self):
        '''
        @Override Starts the service.
        '''
        self.logger.debug("Service starting.")
        self.run_service()
        if self._interrupted:
            self.logger.debug("Service stopping (requested)...")
        else:
            self.logger.debug("Service stopping (finished)...")

    def stop(self):
        '''
        @Override Gracefully exit service
        '''
        self._service_interrupt_event.set()
        self._interrupted = True
