'''
Listens for new client connections and spawns ClientSessions when appropriate.

Created on Mar 24, 2018
@author: Brian Ricks
'''
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
        super(ConnectionManager, self).__init__()

        self._listener = emews.base.multilistener.MultiListener(config, self)

        self._config = config
        self._thread_dispatcher = thread_dispatcher

    def start(self):
        '''
        Starts the ConnectionManager.
        '''
        self._listener.start()  # start the listener

    def stop(self):
        '''
        Stops the ConnectionManager
        '''
        self._listener.stop()  # shut down the listener

    def handle_accepted_connection(self, sock):
        '''
        @Override start a ClientSession with this socket
        '''
        self._thread_dispatcher.dispatch_thread(
            emews.base.clientsession.ClientSession(self._config, sock, self._thread_dispatcher),
            force_start=True)

    def handle_readable_socket(self, sock):
        '''
        @Override not implemented due to listener not using this callback
        '''
        pass
