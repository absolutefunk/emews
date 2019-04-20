"""
Service spawner server.

Created on Apr 19, 2019
@author: Brian Ricks
"""
import struct

import emews.base.enums
import emews.base.baseserv


class ServSpawner(emews.base.baseserv.BaseServ):
    """Classdocs."""

    __slots__ = ('_cb', '_node_id', '_service_id')

    def __init__(self):
        """Constructor."""
        super(ServSpawner, self).__init__()

        self._cb = [None] * emews.base.enums.hub_protocols.ENUM_SIZE
        self._cb.insert(emews.base.enums.hub_protocols.HUB_NODE_ID_REQ, self._register_node_req)
        self._cb.insert(emews.base.enums.hub_protocols.HUB_SERVICE_ID_REQ, self._register_service_req)

        self._node_id = 2     # current unassigned node id
        self._service_id = 2  # current unassigned service id

    def serv_init(self, node_id, session_id):
        """Init of new node-hub session.  Next expected chunk is request from node."""
        return (self._spawn_query, 6)

    def serv_close(self, session_id):
        """Close a session."""
        pass

    def _spawn_query(self, session_id, chunk):
        """
        Process a request sent by a node.

        req_id (2 bytes) + param_s (4 bytes)
        """
        try:
            req_id, param_s = struct.unpack('>HL', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking spawner query: %s", ex)
            return None

        try:
            ret_tup = self._cb[req_id](session_id, param_s)
        except IndexError:
            self.logger.warning("Invalid query id: %d", req_id)

        return ret_tup

    def _spawn_service_req(self, session_id, str_length):
        """Request to spawn a service.  str_length is expected length of service name."""
        return (self._spawn_service_post, str_length)  # send new node id and terminate

    def _spawn_service_post(self, session_id, service_name):
        """Spawn service given."""

        return (struct.pack('>H', emews.base.enums.net_state.STATE_ACK), (None))
