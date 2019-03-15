"""
Provides a centralized point for distributed log collection over a network.

Created on Apr 22, 2018
@author: Brian Ricks
"""
import logging
import pickle
import struct

import emews.base.basehandler


class HandlerLogging(emews.base.basehandler.BaseHandler):
    """Classdocs."""

    __slots__ = ()

    def handle_read(self, chunk):
        """Handle a chunk of data."""
        read_stage = self._state[node_id]['stage']

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
                # TODO: I think the socket closes at this point ...
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
        self.logger.handle(log_record)
