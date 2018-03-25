'''
Controls the execution cycle of a pyCORE service.

Created on Mar 5, 2018

@author: Brian Ricks
'''

import logging
from threading import Event

from mews.core.common.value_sampler import ValueSampler
from mews.core.services.baseservice import BaseService

class ServiceControl(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        # class vars (declared here for readability)
        self._service = None
        self._distribution = None

        # events
        self._event = Event()

    def stop(self):
        '''
        Gracefully exit service
        '''
        self._event.set()
        # stop service (gracefully of course)
        self._service.stop()

    def set_service(self, baseservice):
        '''
        Sets the service to use
        '''
        if not isinstance(baseservice, BaseService):
            logging.error("Passed argument must be of type BaseService.")
            raise ValueError()

        self._service = baseservice

    def set_distribution(self, distribution):
        '''
        sets the distribution from which to sample next service run time
        '''
        if not isinstance(distribution, ValueSampler):
            logging.error("Passed argument must be of type ValueSampler.")
            raise ValueError()

        self._distribution = distribution

    def run(self):
        '''
        Runs the service in a loop based on the distribution
        '''

        while True:
            self._event.wait(self._distribution.next_value())

            if self._event.is_set():
                '''
                We check it here instead of in the loop for two reasons:
                1) The wait needs to be before the service call, so if the
                request comes during the wait, we still need to check the flag
                here anyways to prevent the service from running if flag is set.
                2) If the request comes during service execution and we check
                this in the loop, then the nice "Caught shutdown request" message
                won't be displayed unless we explicitly check why the loop terminated.

                event.wait() will immediately return if event is set
                '''
                logging.info("Caught shutdown request...")
                break

            # Service does not excute in a separate thread (blocking)
            self._service.start()

        logging.info("Exiting...")
