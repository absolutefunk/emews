'''
Base class for pyCORE services

Created on Mar 5, 2018

@author: Brian Ricks
'''

from abc import abstractmethod
import logging
from threading import Event

class BaseService(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self._logger = logging  # replaced by pyCORE logger unless running standalone
        self._needs_config = True  # change to False if no config file needed
        self._config = {}

        self._service_interrupt_event = Event()  # used to interrupt Event.wait() on stop()

    def configure(self, config_file):
        '''
        Configures the service.
        '''

    def needs_config(self):
        '''
        Returns whether this service needs to be configured.
        '''
        return self._needs_config

    def __set_config(self, bool_config):
        '''
        Does this service need to be configured? True = yes, False = no.
        '''
        self._needs_config = bool_config

    def sleep(self, time):
        '''
        Wraps the event.wait().  Convenience method.
        '''
        self._service_interrupt_event.wait(time)

    def start(self):
        '''
        Starts the service.
        '''
        self._logger.info("Service starting.")
        self.run_service()

    @abstractmethod
    def run_service(self):
        '''
        Where the service entrance code goes.  Must be implemented by child class.
        '''
        raise NotImplementedError("Must implement in subclass.")

    def stop(self):
        '''
        Gracefully exit service
        '''
        self._logger.info("Service stopping.")
        self._service_interrupt_event.set()
