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


class NodeData(object):
    """eMews per node data."""

    __slots__ = ('services'    # eMews services running on this node
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

    __slots__ = ('_cb', '_node_id', '_node_cache', '_session_node_id')

    def __init__(self):
        """Constructor."""
        self._cb = [None] * HubProto.ENUM_SIZE
        self._cb.insert(HubProto.HUB_NODE_ID_REQ, self._register_node_req)
        self._cb.insert(HubProto.HUB_CHECK_NODE_ID, self._check_node_id)

        self._node_id = 2  # current unassigned node id
        self._node_cache = {}  # [node_id]: NodeData
        self._session_node_id = {}  # [session_id]: node_id (temp: per session)

    def serv_init(self, node_id, session_id):
        """Init of new node-hub session.  Next expected chunk is request from node."""
        self._session_node_id[session_id] = node_id
        return (self._hub_query, 6)

    def serv_close(self, session_id):
        """Close a session."""
        self._session_node_id.pop(session_id)

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
        """
        Register a new node (post-request).

        Next cb is a confirmation of the node_id.
        """
        new_node_id = struct.pack('>L', self._node_id)
        self._node_id += 1
        return (new_node_id, (self._register_node_conf, 4))

    def _register_node_conf(self, session_id, chunk):
        """Acknowledgment of node_id."""
        try:
            node_id = struct.unpack('>L', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking hub query: %s", ex)
            return None

        if node_id == self._session_node_id[session_id]:
            # node ids match, add new node id
            self._node_cache[node_id] = NodeData()
        else:
            self.logger.warning("node id passed (%d) does not match assigned node id (%d).",
                                node_id, self._session_node_id[session_id])

        # NOTE: it is possible that if a connection terminates before the ACK is received at remote,
        # that the remote will rerequest a new node_id.  If so, then the remote should reconnect and
        # check that the node_id it was given exists.
        ret_data = struct.pack('>H', emews.base.basenet.HandlerCB.STATE_ACK_OK)
        return (ret_data, (None))  # send ACK and close connection

    def _check_node_id(self, session_id, chunk):
        """Check if a node id exists.  chunk = node_id given."""
        if chunk in self._node_cache:
            ret_data = struct.pack('>H', emews.base.basenet.HandlerCB.STATE_ACK_OK)
        else:
            ret_data = struct.pack('>H', emews.base.basenet.HandlerCB.STATE_ACK_NOK)

        return (ret_data, (None))
