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
        self._cb = []
        self._cb.append(self._agent_req_end)  # index [0]

    def serv_init(self, id, node_id, service_id):
        """Init of new agent session.  Next expected chunk is request from remote agent."""
        return (self._agent_request, 4)

    def _agent_request(self, id, chunk):
        """
        Process a request sent by a remote agent.

        req_id (2 bytes) + param_s (2 bytes)
        """
        try:
            req_id, param_s = struct.unpack('>HH', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking agent request: %s", ex)
            return None

        try:
            ret_tup = self._cb[req_id](id, param_s)
        except IndexError:
            self.logger.warning("Invalid request id: %d", req_id)

        return ret_tup

    def _agent_req_end(self, id, param):
        """Remote agent ends the session."""
        return None
