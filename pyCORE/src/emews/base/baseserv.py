"""
Base class for networking servers.

Created on Apr 2, 2019
@author: Brian Ricks
"""
from abc import abstractmethod

import emews.base.meta


class BaseServ:
    """Classdocs."""

    __metaclass__ = emews.base.meta.InjectionMetaWithABC
    __slots__ = ("_sys", "logger", "_ids")

    def __init__(self):
        """Constructor."""
        self._ids = {}  # [session_id]: node_id

    @property
    def sys(self):
        """Return the system properties object."""
        return self._sys

    def handle_init(self, session_id, node_id):
        """Init session_id --> node_id mapping.  Return cb from serv_init()."""
        self._ids[session_id] = node_id
        return self.serv_init

    def handle_close(self, session_id):
        """Session termination."""
        del self._ids[session_id]
        self.serv_close(session_id)

    @abstractmethod
    def serv_init(self, session_id):
        """Return the first callback used for this server."""
        pass

    @abstractmethod
    def serv_close(self, session_id):
        """Handle any session closing tasks."""
        pass

    def get_node_id(self, session_id):
        """Return the node_id associated with the given session_id."""
        return self._ids[session_id]
