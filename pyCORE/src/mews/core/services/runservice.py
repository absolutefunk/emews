'''
Runs a CORE service in a loop.

Created on Mar 5, 2018

@author: Brian Ricks
'''

import importlib
import signal
import sys
from threading import Event

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

        # signals
        signal.signal(signal.SIGINT, self.exit_service)
        signal.signal(signal.SIGTERM, self.exit_service)

        # events
        self._event = Event()

    def exit_service(self, signal_type, frame):
        '''
        When signal caught (SIGINT, SIGTERM), gracefully exit service
        '''
        self._event.set()
        # stop service (gracefully of course)
        self._service.stop()

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
                print "[RunService - run]: Caught shutdown request"
                break

        self._service.start()

        print "[RunService - run]: Exiting..."

if __name__ == '__main__':
    main()

def main():
    '''
    main function
    '''
    arg_map = {}

    if not parseargs(arg_map):
        sys.exit()

    service_module = importlib.import_module(sys.argv[1])

    run_service = RunService()
    run_service.set_service(service_module)

def parseargs(arg_map):
    '''
    Parses command line arguments.  Returns false if something goes awry during
    parsing.

    The basic idea is to take the arg list and parse into k/v pairs based on
    simple rules (ie, key must start with '--').
    '''

    # check for the bare minimum (service arg is present)
    if len(sys.argv) < 2 and not sys.argv[1].startswith("--service "):
        print "[RunService - __main__]: usage: " + sys.argv[0] + "--service <service_module>"
        return False

    return True
