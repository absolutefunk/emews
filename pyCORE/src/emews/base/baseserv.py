"""
Base class for networking servers.

Created on Apr 2, 2019
@author: Brian Ricks
"""
from abc import abstractmethod

import emews.base.baseobject


class BaseServ(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_net_cache')

    def handle_init(self, node_id, session_id):
        """Session init."""
        return self.serv_init(node_id, session_id)

    def handle_close(self, session_id):
        """Session termination."""
        self.serv_close(session_id)

    @abstractmethod
    def serv_init(self, node_id, session_id):
        """Return the first callback used for this server."""
        pass

    @abstractmethod
    def serv_close(self, session_id):
        """Handle any session closing tasks."""
        pass
