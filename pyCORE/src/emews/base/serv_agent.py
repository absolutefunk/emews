"""
Agent server.

Handles agent communication.

Created on Apr 3, 2019
@author: Brian Ricks
"""
import emews.base.baseserv


class ServAgent(emews.base.baseserv.BaseServ):
    """Classdocs."""

    __slots__ = ()

    def serv_init(self, id, node_id, service_id):
        """Init of new agent session.  Next expected chunk is command from remote agent."""
        return (self._agent_command, 1)

    def _agent_command(self, id, chunk):
        """Process a command sent by a remote agent."""
