'''
Provides a centralized point for distributed log collection over a network.

Only one node will have a LogServer.  The system.yml config will specify the node.  The other nodes
will be able to look up the logserver node, and forward log entries to it.

When using distributed logging, the formatting configuration in system.yml would be applied to
LogServer if LogServer is the final destination for the log entries.  If LogServer is acting as a
collection and forward server, then no formatting is applied.

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

        self._listener = emews.base.multiasynclistener.MultiASyncListener(self)

        self._sock_state = {}  # stores state related to individual sockets
        # destination logger to output log entries
        self._dest_logger = logging.LoggerAdapter(logging.getLogger(
            self._config.get_sys('logserver', 'destination_logger')),
                                 {'nodename': self._config.nodename})

    def logger(self):
        '''
        @Override returns the logger assigned to the logserver (destination_logger)
        '''
        return self._dest_logger

    def run_service(self):
        '''
        @Override Called to start execution of implementing task.
        '''

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
                return

            if len(chunk) < 4:
                # doesn't look like the message length
                return

            try:
                slen = struct.unpack('>L', chunk)[0]
            except struct.error as ex:
                self.logger.warning("Struct error when unpacking log message length: %s", ex)
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
                return
            self._sock_state[sock]['msg'] = self._sock_state[sock]['msg'] + chunk

            if len(self._sock_state[sock]['msg']) == len(self._sock_state[sock]['slen']):
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
        self._base_logger.handle(log_record)
