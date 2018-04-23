'''
Listens for new client connections and spawns ClientSessions when appropriate.

Created on Mar 24, 2018

@author: Brian Ricks
'''
import signal

import emews.base.clientsession
import emews.base.spawninglistener
import emews.base.thread_dispatcher

class ConnectionManager(emews.base.spawninglistener.SpawningListener):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(ConnectionManager, self).__init__(config, emews.base.clientsession.ClientSession)

        # register signals
        signal.signal(signal.SIGHUP, self.shutdown_signal_handler)
        signal.signal(signal.SIGINT, self.shutdown_signal_handler)

        # handles thread spawning/management
        self._thread_dispatcher = emews.base.thread_dispatcher.ThreadDispatcher(self.config)

    def shutdown_signal_handler(self, signum, frame):
        '''
        Signal handler for incoming signals (those which may imply we need to shutdown)
        '''
        self.logger.info("Received signum %d, beginning shutdown...", signum)
        self.stop()  # shut down the listener

    def update_spawnclass_args(self):
        '''
        @Override return the ThreadDispatcher, as the ClientSession needs it
        '''
        return [self.dispatcher]
