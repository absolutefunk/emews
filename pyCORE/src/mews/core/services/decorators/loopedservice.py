'''
A decorator that runs a service in a loop, according to a sampler.
This implies that the core functionality of the service itself is not infinite in duration,
but that its behavior needs to be looped for the service duration to be infinite.

Created on Mar 5, 2018

@author: Brian Ricks
'''
from threading import Event

from mews.core.services.decorators.servicedecorator import ServiceDecorator

class LoopedService(ServiceDecorator):
    '''
    classdocs
    '''

    def __init__(self, recipient_service):
        '''
        Constructor
        '''
        ServiceDecorator.__init__(recipient_service)

        self._sampler = None  # get this from the service conf

        # events
        self._event = Event()

    def loop_service(self):
        '''
        Runs the service in a loop based on the sampler
        '''

        while True:
            self._event.wait(self._sampler.next_value())

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
                self.logger.debug("Caught shutdown request...")
                break

            self._service.start()

        self.logger.info("Exiting...")
