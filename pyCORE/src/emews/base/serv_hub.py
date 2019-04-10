"""
Hub server.

Handles core hub related communication.

Created on Apr 9, 2019
@author: Brian Ricks
"""
import struct

import emews.base.baseserv


class NodeData(object):
    """Data specific to a network node."""

    MSG_RO = "NodeData properties are read-only."

    __slots__ = ('addr',     # network address (CORE networks we use have single nics at endpoints)
                 'services'  # eMews services running on this node
                 )

    def __init__(self, **kwargs):
        """Constructor."""
        for key, value in kwargs.iteritems():
            object.__setattr__(self, key, value)

        object.__setattr__(self, 'services', {})  # [service_id]: service_data

    def __setattr__(self, attr, value):
        """Attributes are not mutable."""
        raise AttributeError(NodeData.MSG_RO)

    def add_service(self, service_id):
        """Add a new service_id."""
        self.services[service_id] = None  # TODO: None is just a placeholder ...


class ServHub(emews.base.baseserv):
    """Classdocs."""

    __slots__ = ('_cb', '_node_cache')

    def __init__(self):
        """Constructor."""
        self._cb = []
        self._cb.append(None)  # Index [0]
        self._cb.append(self._register_node_req)  # Index [1]
        self._cb.append(self._register_service_req)  # Index [2]

        self._node_cache = {}  # [node_id]: node_data

    def serv_init(self, session_id):
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
        return (self._register_node_post, 4)

    def _register_service_req(self, session_id, chunk):
        """Register a new service for a node."""
        return (self._register_service_post, 4)

    def _register_node_post(self, session_id, chunk):
        """
        Register a new node (post-request).

        node_addr (4 bytes)
        """
        try:
            node_addr = struct.unpack('>LL', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking hub query: %s", ex)
            return None

        if node_id in self._node_cache:
            self.logger.debug("Node '%d' is already registered.", node_id)
            return None

        self._node_cache[node_id] = NodeData(addr=node_addr)
        self.logger.debug("Node '%d' registered successfully.", node_id)

        # TODO: send new node id to node.

        return None

    def _register_service_post(self, id, chunk):
        """
        Register a new service (post-request).

        service_id (4 bytes)
        """
        try:
            service_id = struct.unpack('>L', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking hub query: %s", ex)
            return None

        try:
            node_id = self.get_node_id(id)
        except KeyError:
            self.logger.debug("Session id '%d' does not map to a node id.", session_id)

        self._node_cache[node_id].add_service(service_id)
        self.logger.debug(
            "Service '%d' for node '%d' registered successfully.", service_id, node_id)

        return None
