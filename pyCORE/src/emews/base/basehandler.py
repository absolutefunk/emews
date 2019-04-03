"""
Base class for networking handlers.

Created on Apr 2, 2019
@author: Brian Ricks
"""
from abc import abstractmethod

import emews.base.meta


class BaseHandler(object):
    """Classdocs."""

    __metaclass__ = emews.base.meta.InjectionMetaWithABC
    __slots__ = ("_sys", "logger", "request_write")

    @property
    def sys(self):
        """Return the system properties object."""
        return self._sys

    @abstractmethod
    def handle_init(self, id):
        """
        Handle any initialization.

        Return type is a tuple: (next_callback, buffer_size).
        """
        pass

    @abstractmethod
    def handle_write(self, id):
        """
        Handle the case when a socket is writable.

        Return type is a string of bytes to send, or None.
        """
        pass

    @abstractmethod
    def handle_close(self, id):
        """Handle the case when a socket is closed.  No return type."""
        pass
