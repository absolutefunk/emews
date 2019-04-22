"""
Provides a centralized point for distributed log collection over a network.

Created on Apr 11, 2019
@author: Brian Ricks
"""
import logging
import pickle
import struct

import emews.base.baseserv


class ServLogging(emews.base.baseserv.BaseServ):
    """Classdocs."""

    __slots__ = ()

    def serv_init(self, node_id, session_id):
        """Return the expected number of bytes to receive first and the callback."""
        return (self._msg_length, 4)

    def serv_close(self, session_id):
        """Handle the case when a socket is closed."""
        pass

    def _msg_length(self, session_id, chunk):
        """Log message length (4 bytes)."""
        try:
            slen = struct.unpack('>L', chunk)[0]
        except struct.error as ex:
            self.logger.warning(
                "Session id: %d, struct error when unpacking log message length: %s",
                session_id, ex)
            return None

        return (self._process_message, slen)

    def _process_message(self, session_id, chunk):
        """Process the complete log message."""
        log_record = logging.makeLogRecord(pickle.loads(chunk))
        self.logger.handle(log_record)
        return (self._msg_length, 4)  # cb for a new message
