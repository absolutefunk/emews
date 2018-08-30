'''
Base class for emews services.
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
    __slots__ = ('_config', '_helpers', '_service_interrupt_event', '_interrupted')

    def __init__(self):
        '''
        Constructor
        '''
        super(BaseService, self).__init__()

        self._config = None  # initialized in _post_init
        self._helpers = None  # initialized in _post_init
        self._service_interrupt_event = Event()  # used to interrupt Event.wait() on stop()
        self._interrupted = False  # set to true on stop()

    def _post_init(self, config, helpers):
        '''
        Injects the configuration after initialization.  Invoked by ServiceBuilder.
        '''
        self._config = config
        self._helpers = helpers

    @property
    def config(self):
        '''
        Returns the config object.
        '''
        return self._config

    @property
    def helpers(self):
        '''
        Returns the helpers object.
        '''
        return self._helpers

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
        if self._interrupted:
            return

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

        if not self._interrupted:
            self.logger.debug("Service stopping (finished)...")
        else:
            self.logger.debug("Service stopping (requested) ...")

    def stop(self):
        '''
        @Override Gracefully exit service
        '''
        self._service_interrupt_event.set()
        self._interrupted = True
