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
    __slots__ = ('sys', 'logger')

    def __init__(self):
        """Constructor."""
        self.logger = emews.base.logger.get_logger()

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
