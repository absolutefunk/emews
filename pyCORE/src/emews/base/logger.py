"""
Base Logger, module level.

Created on Feb 21, 2019
@author: Brian Ricks
"""
import logging.handlers
import struct

import emews.base.basenet


_base_logger = None


def get_logger():
    """Simply returns the base logger."""
    return _base_logger


class DistLogger(logging.handlers.SocketHandler):
    """Provides protocol compability for the SocketHandler class."""

    def __init__(self, node_id):
        """Constructor."""
        self._node_id = node_id  # no __slots__, as base class doesn't use it

    def makePickle(self, record):
        """@Override Prefix bytes representing protocol header."""
        return struct.pack(">HHL", emews.base.basenet.NetProto.NET_LOGGING, 0, self._node_id) + \
            super(DistLogger, self).makePickle(record)
