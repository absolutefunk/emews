'''
A decorator that catches unhandled exceptions from a service.  This is useful for services that
use the LoopedService decorator and should restart after having an exception thrown.
Note: The ordering of application of this decorator is important.  If applied after the
LoopedService decorator, the service will no longer loop if the services throws an unhandled
exception (this decorator will still catch the exeception).

Created on May 21, 2018
@author: Brian Ricks
'''
import emews.services.modifiers.service_modifier

class NoRaiseService(emews.services.modifiers.service_modifier.ServiceModifier):
    '''
    classdocs
    '''
    def start(self):
        '''
        @Override Start the service, with additional code to handle uncaught exceptions.
        '''
        try:
            super(NoRaiseService, self).start()
        except Exception as ex:  # pylint: disable=W0703
            self.logger.error("[%s] Raised exception: %s",
                              self._recipient_service.__class__.__name__, ex)
            # Do not raise again, just exit.
