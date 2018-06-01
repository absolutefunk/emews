'''
Provides a centralized point for distributed log collection over a network.

Only one node will have a LogServer.  The system.yml config will specify the node.  The other nodes
will be able to look up the logserver node, and forward log entries to it.

When using distributed logging, the formatting configuration in system.yml would be applied to
LogServer if LogServer is the final destination for the log entries.  If LogServer is acting as a
collection and forward server, then no formatting is applied.

Note:  For the node running the LogServer, when the listener is starting up, any log messages that
are generated before the listener is running, will be dropped as the listener won't be running to
receive them.  These should only be error messages which will raise exceptions anyway.

Created on Apr 22, 2018
@author: Brian Ricks
'''
import logging
import pickle
import socket
import struct

import emews.base.ihandlerlistener
import emews.base.multiasynclistener
import emews.services.baseservice

class LogServer(emews.services.baseservice.BaseService,
                emews.base.ihandlerlistener.IHandlerListener):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(LogServer, self).__init__(config)

        # we need to create a config for the listener, as it uses the logger network handler config
        listener_config_dict = {
            'config': {
                'host': self.config.get_sys('logging', 'log_conf', 'handlers', 'network', 'host'),
                'port': self.config.get_sys('logging', 'log_conf', 'handlers', 'network', 'port')
            }
        }
        listener_config = self.config.clone_with_dict(listener_config_dict)

        try:
            self._listener = emews.base.multiasynclistener.MultiASyncListener(listener_config, self)
        except socket.error as ex:
            print "Could not instantiate LogServer Listener: " + ex
            raise

        self._sock_state = {}  # stores state related to individual sockets
        # destination logger to output log entries
        self._dest_logger = logging.getLogger(
            self.config.get_sys('logserver', 'destination_logger'))

    def run_service(self):
        '''
        @Override Called to start execution of implementing task.  Start the listener.
        '''
        self._listener.start()

    def stop(self):
        '''
        @Override Stops the listener.
        '''
        self._listener.stop()

    def handle_accepted_connection(self, sock):
        '''
        @Override Called when a socket is first accepted.
        '''
        self._sock_state[sock] = {}
        self._sock_state[sock]['stage'] = 0  # stage in the receive process

    def handle_readable_socket(self, sock):
        '''
        @Override Called when a socket has data to be read.
        '''
        # Get the stage of the socket, and process accordingly.
        read_stage = self._sock_state[sock]['stage']
        if read_stage == 0:
            # get log message length (4 bytes)
            try:
                chunk = sock.recv(4)
            except socket.error as ex:
                self.logger.warning("Socket error when receiving message length: %s", ex)
                self._listener.request_close(sock)
                return

            if len(chunk) < 4:
                #  Most likely because the connection was closed
                # at the client end.  This is expected as after a message is fully received, the
                # stage resets back to 0
                self._listener.request_close(sock)
                return

            try:
                slen = struct.unpack('>L', chunk)[0]
            except struct.error as ex:
                self.logger.warning("Struct error when unpacking log message length: %s", ex)
                self._listener.request_close(sock)
                return

            self._sock_state[sock]['slen'] = slen
            self._sock_state[sock]['stage'] = 1
            self._sock_state[sock]['msg'] = ""

        elif read_stage == 1:
            try:
                chunk = sock.recv(
                    self._sock_state[sock]['slen'] - len(self._sock_state[sock]['msg']))
            except socket.error as ex:
                self.logger.warning("Socket error when receiving log message: %s", ex)
                self._sock_state[sock]['stage'] = 0
                self._sock_state[sock]['msg'] = ""
                self._listener.request_close(sock)
                return

            if not chunk:
                # This is unexpected.  Could be a connection problem.
                self.logger.warning("Socket read buffer is empty when expecting logging data.  "\
                    "Closing socket ...")
                self._listener.request_close(sock)
                return

            self._sock_state[sock]['msg'] = self._sock_state[sock]['msg'] + chunk

            if len(self._sock_state[sock]['msg']) == self._sock_state[sock]['slen']:
                # received the entire message
                self.process_message(self._sock_state[sock]['msg'])  # handle the msg
                self._sock_state[sock]['stage'] = 0
                self._sock_state[sock]['msg'] = ""

    def process_message(self, msg):
        '''
        Processes the complete log message.
        '''
        # TODO: Instantiate another listener on a different port to listen for incoming logging
        # clients.  If any logging clients are connected, then route messages to the client
        # (no struct unpacking, no unpickle, just send struct and pickle directly).
        log_record = logging.makeLogRecord(pickle.loads(msg))
        self._dest_logger.handle(log_record)
