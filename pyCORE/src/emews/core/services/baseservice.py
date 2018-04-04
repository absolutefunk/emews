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

import emews.core.config
import emews.core.services.iservice

class BaseService(emews.core.services.iservice.IService):
    '''
    classdocs
    '''
    def __init__(self, service_config):
        '''
        Constructor
        The service_config contains system config information (such as logging), and any service
        specific configuration information.
        '''
        self._config = service_config
        self._logger = self._config.logger
        self._service_interrupt_event = Event()  # used to interrupt Event.wait() on stop()

        # TODO: In standalone mode, REMOVE_THREAD_CALLBACK is not needed.  Perhaps a key in
        # sys_config to let service know if it was spawned through ServiceManager or standalone?

    @property
    def config(self):
        '''
        @Override Returns the service config object.
        '''
        return self._config

    @property
    def logger(self):
        '''
        @Override Returns the logging object.
        '''
        return self._logger

    @property
    def interrupted(self):
        '''
        Returns true if the service has been interrupted (requested to stop).  Uses events.
        '''
        return self._service_interrupt_event.is_set

    def sleep(self, time):
        '''
        @Override Wraps the event.wait().  Convenience method.
        '''
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
        self._logger.info("Service starting.")
        self.run_service()

    def stop(self):
        '''
        @Override Gracefully exit service
        '''
        self._logger.info("Service stopping.")
        self._service_interrupt_event.set()
