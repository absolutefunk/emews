'''
A decorator that catches unhandled exceptions from a service.  This is useful for services that
use the LoopedService decorator and should restart after having an exception thrown.
Note: The ordering of application of this decorator is important.  If applied after the
LoopedService decorator, the service will no longer loop if the services throws an unhandled
exception (this decorator will still catch the exeception).

Created on May 21, 2018
@author: Brian Ricks
'''
from emews.services.decorators.servicedecorator import ServiceDecorator

class NoRaiseService(ServiceDecorator):
    '''
    classdocs
    '''
    def __init__(self, recipient_service):  # pylint: disable=W0235
        '''
        Constructor
        '''
        super(NoRaiseService, self).__init__(recipient_service)

    def start(self):
        '''
        @Override Starts the service, with additional code to handle uncaught exceptions.
        '''
        try:
            super(NoRaiseService, self).start()
        except Exception as ex:  # pylint: disable=W0703
            self.logger.error("Service raised exception: %s", ex)
            # Do not raise again, just exit.  If LoopedService is a child, then it'll restart
            # This decorator.
