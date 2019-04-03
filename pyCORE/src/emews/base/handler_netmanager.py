"""
Network handler for node to node communication.

Created on March 20, 2019
@author: Brian Ricks
"""

import emews.base.basehandler


class HandlerNetManager(emews.base.basehandler.BaseHandler):
    """Classdocs."""

    __slots__ = ()

    def handle_init(self, id):
        """Return number of bytes expected (buf) to determine protocol."""
        return (self._proto_dispatch, 1)

    def handle_write(self, id):
        """Handle the case when a socket is writable."""
        pass

    def handle_close(self, id):
        """Handle the case when a socket is closed."""
        pass

    def _proto_dispatch(self, id, chunk):
        """Chunk contains the protocol.  Dispatch appropriate handler."""
        pass
