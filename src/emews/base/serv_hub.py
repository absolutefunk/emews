"""
Hub server.

Handles core hub related communication.

Created on Apr 9, 2019
@author: Brian Ricks
"""
import emews.base.enums
import emews.base.baseserv
import emews.base.queryserv
import emews.base.netserv


class ServHub(emews.base.queryserv.QueryServ):
    """Classdocs."""

    __slots__ = ('_node_id', '_service_id')

    @classmethod
    def build_protocols(cls):
        """Build the protocols for this server, and add them to BaseServ.protocols."""
        proto_id = emews.base.enums.net_protocols.NET_HUB
        cls.protocols[proto_id] = [None] * emews.base.enums.hub_protocols.ENUM_SIZE

        new_proto = emews.base.baseserv.NetProto(
            '', type_return='L',
            proto_id=proto_id,
            request_id=emews.base.enums.hub_protocols.HUB_NODE_ID_REQ)
        cls.protocols[proto_id][new_proto.request_id] = new_proto

        new_proto = emews.base.baseserv.NetProto(
            '', type_return='L',
            proto_id=proto_id,
            request_id=emews.base.enums.hub_protocols.HUB_SERVICE_ID_REQ)
        cls.protocols[proto_id][new_proto.request_id] = new_proto

    def __init__(self):
        """Constructor."""
        super(ServHub, self).__init__()

        self.handlers = [None] * emews.base.enums.hub_protocols.ENUM_SIZE
        proto_id = emews.base.enums.net_protocols.NET_HUB

        request_id = emews.base.enums.hub_protocols.HUB_NODE_ID_REQ
        self.handlers[request_id] = emews.base.baseserv.Handler(self.protocols[proto_id][request_id], self._node_id_req)

        request_id = emews.base.enums.hub_protocols.HUB_SERVICE_ID_REQ
        self.handlers[request_id] = emews.base.baseserv.Handler(self.protocols[proto_id][request_id], self._service_id_req)

        self._node_id = 2     # current unassigned node id
        self._service_id = 2  # current unassigned service id

        # we are the hub node, so use a direct query instead of connecting to myself
        self._net_client.hub_query = self.direct_hub_query

        # register my node id
        node_data = emews.base.netserv.NetCache.NodeData()
        self._net_cache.node[1] = node_data

    def serv_init(self, node_id, session_id):
        """Init of new node-hub session."""
        pass

    def serv_close(self, session_id):
        """Close a session."""
        pass

    def _node_id_req(self, session_id):
        """Register a new node."""
        new_node_id = self._node_id
        self._net_cache.add_node(new_node_id, session_id)
        self.logger.info("New node id '%d' given to node using session id: %d",
                         self._node_id, session_id)

        self._node_id += 1

        return (new_node_id, None)  # send new node id and terminate

    def _service_id_req(self, session_id):
        """Register a new service specific to a node."""
        new_service_id = self._service_id
        self._service_id += 1

        node_id = self._net_cache.session[session_id].node_id
        self._net_cache.node[node_id].services.add(new_service_id)

        self.logger.info("New service id '%d' given to node with id '%d' using session id: %d",
                         new_service_id, node_id, session_id)

        return (new_service_id, None)  # send new service id and terminate

    def direct_hub_query(self, request):
        """Hub query method that the hub node uses instead of the netclient version."""
        self._net_cache.session[-1] = emews.base.netserv.NetCache.SessionData()
        self._net_cache.session[-1].node_id = 1

        ret = self.handlers[request].callback(-1)[0]

        del self._net_cache.session[-1]

        return ret
