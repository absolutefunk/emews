'''
A decorator that runs a service in a loop, according to a sampler.
This implies that the core functionality of the service itself is not infinite in duration,
but that its behavior needs to be looped for the service duration to be infinite.

Created on Mar 5, 2018
@author: Brian Ricks
'''
from emews.services.decorators.servicedecorator import ServiceDecorator

class LoopedService(ServiceDecorator):
    '''
    classdocs
    '''
    def __init__(self, recipient_service):
        '''
        Constructor
        '''
        super(LoopedService, self).__init__(recipient_service)

        try:
            self._sampler = self.dependencies.get('loop_sampler')
        except ValueError as ex:
            self.logger.error(ex)
            raise

    def start(self):
        '''
        @Override Starts the service, with additional code for the looping.
        '''
        self.loop_service()

    def loop_service(self):
        '''
        Runs the service in a loop based on the sampler
        '''
        while True:
            self.sleep(self._sampler.next_value())

            if self.interrupted:
                '''
                The wait needs to be before the service call, so if the interrupt
                request comes during the wait, we still need to check the flag
                here anyways to prevent the service from running if interrupted.
                Note:  The current implementation of sleep() uses events, so once
                interrupted (event.set()), then sleep will immediately return on future
                calls.
                '''
                self.logger.debug("Caught shutdown request...")
                break
            try:
                super(LoopedService, self).start()
            except StandardError:
                self.logger.error("Service raised exception.  Stopping loop ...")
                raise

        self.logger.info("Exiting loop ...")
