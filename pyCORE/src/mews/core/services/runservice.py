'''
Created on Mar 5, 2018

@author: Brian Ricks
'''

import signal
import time

from mews.core.common.value_sampler import ValueSampler
from mews.core.services.baseservice import BaseService

class RunService(object):
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
        self._keep_looping = True

        # signals
        signal.signal(signal.SIGINT, self.exit_service)
        signal.signal(signal.SIGTERM, self.exit_service)

    def exit_service(self):
        '''
        When signal caught (SIGINT, SIGTERM), gracefully exit service
        '''
        self._keep_looping = False

    def set_service(self, baseservice):
        '''
        Sets the service to use
        '''
        if not isinstance(baseservice, BaseService):
            raise ValueError("[RunService - set_service]: Passed argument \
                    must be of type BaseService.")

        self._service = baseservice

    def set_distribution(self, distribution):
        '''
        sets the distribution from which to sample next service run time
        '''
        if not isinstance(distribution, ValueSampler):
            raise ValueError("[RunService - set_distribution]: Passed argument \
                    must be of type ValueSampler.")

        self._distribution = distribution

    def run(self):
        '''
        Runs the service in a loop based on the distribution
        '''
        while self._keep_looping:
            time.sleep(self._distribution.next_value())
            self._service.start()

        print "[RunService - run]: Exiting..."
