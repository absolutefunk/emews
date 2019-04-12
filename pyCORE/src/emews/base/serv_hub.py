"""
Hub server.

Handles core hub related communication.

Created on Apr 9, 2019
@author: Brian Ricks
"""
import struct

import emews.base.baseserv


class HubProto(object):
    """Enumerations for supported hub requests."""

    __slots__ = ()

    ENUM_SIZE = 2

    HUB_NONE = 0         # placeholder
    HUB_NODE_ID_REQ = 1  # Request node id

class NodeData(object):
    """eMews per node data."""

    __slots__ = ('session_id'  # current session_id (or None)
                 'services'    # eMews services running on this node
                 )

    def __init__(self, **kwargs):
        """Constructor."""
        self.session_id = None
        self.services = {}  # [service_id]: service_data

    def add_service(self, service_id):
        """Add a new service_id."""
        self.services[service_id] = None  # TODO: None is just a placeholder ...


class ServHub(emews.base.baseserv):
    """Classdocs."""

    __slots__ = ('_cb', '_node_cache')

    def __init__(self):
        """Constructor."""
        self._cb = [None] * HubProto.ENUM_SIZE
        self._cb.insert(HubProto.HUB_NODE_ID_REQ, self._register_node_req)

        self._node_cache = {}  # [node_id]: NodeData

    def serv_init(self, node_id, session_id):
        """Init of new node-hub session.  Next expected chunk is request from node."""
        return (self._hub_query, 4)

    def _hub_query(self, session_id, chunk):
        """
        Process a request sent by a node.

        req_id (2 bytes) + param_s (2 bytes)
        """
        try:
            req_id, param_s = struct.unpack('>HH', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking hub query: %s", ex)
            return None

        try:
            ret_tup = self._cb[req_id](session_id, param_s)
        except IndexError:
            self.logger.warning("Invalid query id: %d", req_id)

        return ret_tup

    def _register_node_req(self, session_id, chunk):
        """Register a new node (request)."""
        return (self._register_node_post, 0)  # write mode

    def _register_node_post(self, session_id, chunk):
        """Register a new node (post-request)."""
        return (new_node_id, None)  # None specifies to close connection after write
