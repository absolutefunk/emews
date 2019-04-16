"""
Hub server.

Handles core hub related communication.

Created on Apr 9, 2019
@author: Brian Ricks
"""
import struct

import emews.base.basenet
import emews.base.baseserv


class HubProto(object):
    """Enumerations for supported hub requests."""

    __slots__ = ()

    ENUM_SIZE = 3

    HUB_NONE = 0           # placeholder
    HUB_NODE_ID_REQ = 1    # Request node id
    HUB_CHECK_NODE_ID = 2  # check if a node id is registered


class ServHub(emews.base.baseserv):
    """Classdocs."""

    __slots__ = ('_cb', '_node_id')

    def __init__(self):
        """Constructor."""
        self._cb = [None] * HubProto.ENUM_SIZE
        self._cb.insert(HubProto.HUB_NODE_ID_REQ, self._register_node_req)
        self._cb.insert(HubProto.HUB_CHECK_NODE_ID, self._check_node_id)

        self._node_id = 2  # current unassigned node id

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
        self.net_cache.add_node(self._node_id, session_id)
        self._node_id += 1
        return (new_node_id, (None))  # send new node id and terminate
