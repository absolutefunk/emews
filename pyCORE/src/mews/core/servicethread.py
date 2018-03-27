'''
Provides functionality in a separate thread for socket communication between ServiceManager's
listener and a client.  If client sends a service to run, then this class will contain a
ServiceControl object which itself will contain the requested service.

Created on Mar 27, 2018

@author: Brian Ricks
'''
from mews.core.services.basethread import BaseThread

class ServiceThread(BaseThread):
    '''
    classdocs
    '''

    def __init__(self, logbase, name, cmd_sock, reg_cb):
        '''
        Constructor
        '''
        BaseThread.__init__(self, logbase, name)

        self._command_sock = cmd_sock  # socket used to receive commands
        self._callback_register = reg_cb  # to register self
        self._service_control = None

    def run_service(self):
        '''
        @Override of run_service method in BaseThread
        '''

        self._command_sock.close()
        self._command_sock = None

    def stop(self):
        '''
        When invoked, lets this thread know to start shutting down
        '''
        if self._service_control is None:
            raise ValueError("No ServiceControl attached to this ServiceThread.")

        self._logger.debug("(%s) Passing stop request to ServiceControl.", self.name)
        self._service_control.stop()
