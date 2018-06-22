'''
Listens for new client connections and spawns ClientSessions when appropriate.

Created on Mar 24, 2018
@author: Brian Ricks
'''
import signal

import emews.base.baseobject
import emews.base.clientsession
import emews.base.ihandlerlistener
import emews.base.multilistener

class ConnectionManager(emews.base.baseobject.BaseObject,
                        emews.base.ihandlerlistener.IHandlerListener):
    '''
    classdocs
    '''
    def __init__(self, config, thread_dispatcher):
        '''
        Constructor
        '''
        # register signals
        signal.signal(signal.SIGHUP, self.shutdown_signal_handler)
        signal.signal(signal.SIGINT, self.shutdown_signal_handler)

        super(ConnectionManager, self).__init__(config)

        self._listener = emews.base.multilistener.MultiListener(
            self.config.get_sys_new('listener'), self)

        self._thread_dispatcher = thread_dispatcher

    def shutdown_signal_handler(self, signum, frame):
        '''
        Signal handler for incoming signals (those which may imply we need to shutdown)
        '''
        self.logger.info("Received signum %d, beginning shutdown...", signum)
        self._listener.stop()  # shut down the listener

    def start(self):
        '''
        Starts the ConnectionManager.
        '''
        try:
            self._listener.start()
        except StandardError as ex:
            self.logger.error("Listener failed: %s", ex)
            raise

    def handle_accepted_connection(self, sock):
        '''
        @Override start a ClientSession with this socket
        '''
        self._thread_dispatcher.dispatch_thread(
            emews.base.clientsession.ClientSession(self.config.get_sys_new('listener'), sock,
                                                   self._thread_dispatcher),
            force_start=True)

    def handle_readable_socket(self, sock):
        '''
        @Override not implemented due to listener not using this callback
        '''
        pass
