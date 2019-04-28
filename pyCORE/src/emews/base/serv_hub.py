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

    def __init__(self, net_client):
        """Constructor."""
        super(ServHub, self).__init__()

        self.handlers = [None] * emews.base.enums.hub_protocols.ENUM_SIZE
        self.handlers[emews.base.enums.hub_protocols.HUB_NODE_ID_REQ] = \
            emews.base.baseserv.Handler(self._node_id_req, '', send_type_str='L')
        self.handlers[emews.base.enums.hub_protocols.HUB_SERVICE_ID_REQ] = \
            emews.base.baseserv.Handler(self._service_id_req, '', send_type_str='L')

        self._node_id = 2     # current unassigned node id
        self._service_id = 2  # current unassigned service id

        # we are the hub node, so use a direct query instead of connecting to myself
        net_client.hub_query = self.direct_hub_query

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

        return (new_service_id, None)  # send new service id and terminate

    def direct_hub_query(self, request):
        """Hub query method that the hub node uses instead of the netclient version."""
        self._net_cache.session[-1] = emews.base.netserv.NetCache.SessionData()
        self._net_cache.session[-1].node_id = 1

        ret = self.handlers[request].callback(-1)

        del self._net_cache.session[-1]

        return ret
