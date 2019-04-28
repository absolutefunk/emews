"""
Provides a centralized point for distributed log collection over a network.

Created on Apr 11, 2019
@author: Brian Ricks
"""
import logging
import pickle

import emews.base.baseserv


class ServLogging(emews.base.baseserv.BaseServ):
    """Classdocs."""

    __slots__ = ()

    def __init__(self):
        """Constructor."""
        super(ServLogging, self).__init__()
        self.handlers = emews.base.baseserv.Handler(self._process_message, 's')

    def serv_init(self, node_id, session_id):
        """Return the expected number of bytes to receive first and the callback."""
        return self.handlers

    def serv_close(self, session_id):
        """Handle the case when a socket is closed."""
        pass

    def _process_message(self, session_id, msg):
        """Process the complete log message."""
        log_record = logging.makeLogRecord(pickle.loads(msg))
        self.logger.logger.handle(log_record)
        return self.handlers
