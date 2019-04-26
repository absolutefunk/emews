"""
Agent server.

Handles agent communication on the hub.

Created on Apr 3, 2019
@author: Brian Ricks
"""
import struct

import emews.base.baseserv


class ServAgent(emews.base.baseserv.BaseServ):
    """Classdocs."""

    __slots__ = ('_cb')

    def __init__(self):
        """Constructor."""
        super(ServAgent, self).__init__()

        self._cb = []
        self._cb.append(self._agent_req_end)  # index [0]

    def serv_init(self, id, node_id, service_id):
        """Init of new agent session.  Next expected chunk is request from remote agent."""
        return (self._agent_query, 6)

    def serv_close(self, session_id):
        """Close a session."""
        pass

    def _agent_query(self, session_id, chunk):
        """
        Process a request sent by a node.

        req_id (2 bytes) + param_s (4 bytes)
        """
        try:
            req_id, param_s = struct.unpack('>HL', chunk)
        except struct.error as ex:
            self.logger.warning("Session id: %d, struct error when unpacking agent query: %s",
                                session_id, ex)
            return None

        try:
            ret_tup = self._cb[req_id](session_id, param_s)
        except IndexError:
            self.logger.warning("Session id: %d, invalid query id: %d", session_id, req_id)

        return ret_tup

    def _agent_req_end(self, id, param):
        """Remote agent ends the session."""
        return None
