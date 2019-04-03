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

    def handle_init(self, id):
        """Return the expected number of bytes to receive first and the callback."""
        return (self._msg_length, 4)

    def handle_write(self, id):
        """Handle the case when a socket is writable."""
        pass

    def handle_close(self, id):
        """Handle the case when a socket is closed."""
        pass

    def _msg_length(self, id, chunk):
        """Log message length (4 bytes)."""
        try:
            slen = struct.unpack('>L', chunk)[0]
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking log message length: %s", ex)
            return None

        return (self._process_message, slen)

    def _process_message(self, id, chunk):
        """Process the complete log message."""
        log_record = logging.makeLogRecord(pickle.loads(chunk))
        self.logger.handle(log_record)
        return (self._msg_length, 4)
