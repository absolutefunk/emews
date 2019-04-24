"""
Base Logger, module level.

Created on Feb 21, 2019
@author: Brian Ricks
"""
import logging.handlers
import struct

import emews.base.enums


_base_logger = None


def get_logger():
    """Simply returns the base logger."""
    return _base_logger


class DistLogger(logging.handlers.SocketHandler):
    """Provides protocol compability for the SocketHandler class."""

    def __init__(self, host, port, node_id):
        """Constructor."""
        super(DistLogger, self).__init__(host, port)
        self._node_id = node_id  # no __slots__, as base class doesn't use it

    def createSocket(self):
        """@Override send proto and node id upon successful connection."""
        super(DistLogger, self).createSocket()
        if self.sock:
            # send the proto id (logging) and node id to hub first
            try:
                self.sock.sendall(
                    struct.pack(">HL", emews.base.enums.net_protocols.NET_LOGGING, self._node_id))
            except OSError:  # pragma: no cover
                self.sock.close()
                self.sock = None  # so we can call createSocket next time
