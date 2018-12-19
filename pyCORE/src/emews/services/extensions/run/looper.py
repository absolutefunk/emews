"""
eMews Service Extension

Runs a service in a loop, according to a sampler.  This implies that the core functionality of the
service itself is not infinite in duration, but that its behavior needs to be looped for the service
duration to be infinite.

Created on Mar 5, 2018
@author: Brian Ricks
"""
import emews.services.extensions.service_extension

class Looper(emews.services.extensions.service_extension.ServiceExtension):
    '''
    classdocs
    '''
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
            self.sleep(self.helpers.loop_sampler.sample())

            if self.interrupted:
                '''
                The wait needs to be before the service call, so if the interrupt
                request comes during the wait, we still need to check the flag
                here anyways to prevent the service from running if interrupted.
                Note:  The current implementation of sleep() uses events, so once
                interrupted (event.set()), then sleep will immediately return on future
                calls.
                '''
                self.logger.debug("Caught shutdown request ...")
                break

            super(Looper, self).start()

        self.logger.info("Exiting loop ...")
