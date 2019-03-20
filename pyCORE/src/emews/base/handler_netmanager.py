"""
Network handler for node to node communication.

Created on March 20, 2019
@author: Brian Ricks
"""

from emews.base.connectionmanager import HandlerCB


class HandlerNetManager(object):
    """Classdocs."""

    __slots__ = ('_sys')

    def __init__(self, sysprop):
        """Constructor."""
        self._sys = sysprop

    def handle_init(self, state_dict):
        """Initialize state dict."""
        pass

    def handle_read(self, chunk, state_dict):
        """Handle a chunk of data."""
        return HandlerCB.NO_REQUEST

    def handle_write(self, state_dict):
        """Handle a writable event."""
        return HandlerCB.NO_REQUEST
