"""
eMews Service Modifier.

Runs a service in a loop, according to a sampler.  This implies that the core functionality of the
service itself is not infinite in duration, but that its behavior needs to be looped for the service
duration to be infinite.

Created on Mar 5, 2018
@author: Brian Ricks
"""
import emews.services.components.common
import emews.services.modifiers.service_modifier


class Looper(emews.services.modifers.service_modifier.ServiceModifier):
    """classdocs."""

    __slots__ = ('_loop_sampler')

    def __init__(self, config):
        """Constructor."""
        super(Looper, self).__init__()
        self._loop_sampler = emews.services.components.common.instantiate(config['loop_sampler'])

    def start(self):
        """@Override Run the service in a loop, based on the sampler."""
        while True:
            self.sleep(self._loop_sampler.sample())

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
