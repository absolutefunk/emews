"""
Base class for networking servers.

Created on Apr 2, 2019
@author: Brian Ricks
"""
from abc import abstractmethod

import emews.base.logger
import emews.base.meta


class BaseServ(object):
    """Classdocs."""

    __metaclass__ = emews.base.meta.InjectionMetaWithABC
    __slots__ = ('sys', 'logger', '_ids')

    def __init__(self):
        """Constructor."""
        self.logger = emews.base.logger.get_logger()
        self._ids = {}  # [session_id]: node_id

    def handle_init(self, session_id, node_id):
        """Init session_id --> node_id mapping.  Return cb from serv_init()."""
        self._ids[session_id] = node_id
        return self.serv_init(node_id, session_id)

    def handle_close(self, session_id):
        """Session termination."""
        del self._ids[session_id]
        self.serv_close(session_id)

    @abstractmethod
    def serv_init(self, node_id, session_id):
        """Return the first callback used for this server."""
        pass

    @abstractmethod
    def serv_close(self, node_id, session_id):
        """Handle any session closing tasks."""
        pass
