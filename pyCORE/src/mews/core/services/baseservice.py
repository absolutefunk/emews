'''
Base class for pyCORE services.
While this class is abstract, it still inherits the IService interface.  This is mainly to
separate base service functionality from the service decorators, which would be redundant otherwise.
Also instantiating decorators would be awkward if the base decorator had to call the BaseService
contructor.

Created on Mar 5, 2018

@author: Brian Ricks
'''

from abc import abstractmethod
import logging
from threading import Event

import mews.core.config
import mews.core.services.iservice

class BaseService(mews.core.services.iservice.IService):
    '''
    classdocs
    '''
    def __init__(self, sys_config, service_config_path=None):
        '''
        Constructor
        If service_config_path=None, implies that service does not need to be configured (outside of
        any sys_config parameters).
        sys_config provides pyCORE relevant configuration (may or may not be relevant to a service).
        '''
        self._logger = logging.getLogger(sys_config.logbase)
        self._service_interrupt_event = Event()  # used to interrupt Event.wait() on stop()

        self._config = mews.core.config.parse(mews.core.config.prepend_path(service_config_path))

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

    @abstractmethod
    def run_service(self):
        '''
        Where the service entrance code goes.  Must be implemented by child class.
        '''
        pass

    def sleep(self, time):
        '''
        Wraps the event.wait().  Convenience method.
        '''
        self._service_interrupt_event.wait(time)

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
