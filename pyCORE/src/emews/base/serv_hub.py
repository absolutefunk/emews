"""
Hub server.

Handles core hub related communication.

Created on Apr 9, 2019
@author: Brian Ricks
"""
import struct

import emews.base.enums
import emews.base.baseserv


class ServHub(emews.base.baseserv.BaseServ):
    """Classdocs."""

    __slots__ = ('_cb', '_node_id', '_service_id')

    def __init__(self):
        """Constructor."""
        self._cb = [None] * emews.base.enums.hub_protocols.ENUM_SIZE
        self._cb.insert(emews.base.enums.hub_protocols.HUB_NODE_ID_REQ, self._register_node_req)
        self._cb.insert(emews.base.enums.hub_protocols.HUB_SERVICE_ID_REQ, self._register_service_req)

        self._node_id = 2     # current unassigned node id
        self._service_id = 2  # current unassigned service id

    def serv_init(self, node_id, session_id):
        """Init of new node-hub session.  Next expected chunk is request from node."""
        return (self._hub_query, 6)

    def serv_close(self, session_id):
        """Close a session."""
        pass

    def _hub_query(self, session_id, chunk):
        """
        Process a request sent by a node.

        req_id (2 bytes) + param_s (4 bytes)
        """
        try:
            req_id, param_s = struct.unpack('>HL', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking hub query: %s", ex)
            return None

        try:
            ret_tup = self._cb[req_id](session_id, param_s)
        except IndexError:
            self.logger.warning("Invalid query id: %d", req_id)

        return ret_tup

    def _register_node_req(self, session_id, chunk):
        """Register a new node (post-request)."""
        new_node_id = struct.pack('>L', self._node_id)
        self._node_id += 1

        self.net_cache.add_node(self._node_id, session_id)

        return (new_node_id, (None))  # send new node id and terminate

    def _register_service_req(self, session_id, chunk):
        """Register a new service specific to a node (post-request)."""
        new_service_id = struct.pack('>L', self._service_id)
        self._service_id += 1

        node_id = self._net_cache.session[session_id].node_id
        self._net_cache.node[node_id].services.add(new_service_id)

        return (new_service_id, (None))  # send new service id and terminate
