"""
Network handler for node to node communication.

Created on March 20, 2019
@author: Brian Ricks
"""
import socket
import struct

import emews.base.baseobject
import emews.base.enums
import emews.base.serv_agent
import emews.base.serv_hub
import emews.base.serv_logging
import emews.base.serv_spawner


class NonSupportedHub(object):
    """Server for hub-based requests to non-hub nodes."""

    def handle_init(self, node_id, session_id):
        """Not the hub, server is not running."""
        self.logger.warning("This protocol server not running: this node is not the hub.")
        return None


class NonSupportedInvalid(object):
    """Server for invalid requests."""

    def handle_init(self, node_id, session_id):
        """Invalid protocol id (or reserved)."""
        self.logger.warning("Protocol not supported or reserved.")
        return None


class NetCache(object):
    """Network cache."""

    class NodeData(object):
        """Per node data."""

        __slots__ = ('addr', 'services')

        def __init__(self):
            """Constructor."""
            self.addr = None       # last known network address associated with this node
            self.services = set()  # set of all services associated with this node

    class SessionData(object):
        """Per session data."""

        __slots__ = ('addr', 'node_id', 'handler')

        def __init__(self):
            """Constructor."""
            self.addr = None       # network address of this session
            self.node_id = None    # node id associated with this session
            self.handler = None    # server or client handling this session

    __slots__ = ('node', 'session')

    def __init__(self):
        """Constructor."""
        self.node = {}    # [node_id]: [services]
        self.session = {}  # [session_id]: SessionData

    def add_node(self, node_id, session_id):
        """
        Add a new node to the cache.

        session_id is assumed to exist and belong to the node_id passed
        """
        node_data = NetCache.NodeData()
        node_data.addr = self.session[session_id].addr  # last known address for this node
        self.node[node_id] = node_data


class NetServ(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_proto_cb', '_net_cache')

    def __init__(self, thread_dispatcher, net_client):
        """Constructor."""
        super(NetServ, self).__init__()

        self._net_cache = NetCache()  # net cache shared among the servers

        nonsupported_invalid = NonSupportedInvalid()
        nonsupported_hub = NonSupportedHub()
        # protocol mappings
        self._proto_cb = [None] * emews.base.enums.net_protocols.ENUM_SIZE
        self._proto_cb[emews.base.enums.net_protocols.NET_NONE] = nonsupported_invalid
        self._proto_cb[emews.base.enums.net_protocols.NET_CC_1] = nonsupported_invalid
        self._proto_cb[emews.base.enums.net_protocols.NET_CC_2] = nonsupported_invalid

        inject_par = {'sys': self.sys, '_net_cache': self._net_cache, '_net_client': net_client}

        if self.sys.is_hub:
            # Hub node runs the following servers:
            self._proto_cb[emews.base.enums.net_protocols.NET_HUB] = \
                emews.base.serv_hub.ServHub(_inject=inject_par)
            self._proto_cb[emews.base.enums.net_protocols.NET_LOGGING] = \
                emews.base.serv_logging.ServLogging(_inject=inject_par)
            self._proto_cb[emews.base.enums.net_protocols.NET_AGENT] = \
                emews.base.serv_agent.ServAgent(_inject=inject_par)
        else:
            self._proto_cb[emews.base.enums.net_protocols.NET_HUB] = nonsupported_hub
            self._proto_cb[emews.base.enums.net_protocols.NET_LOGGING] = nonsupported_hub
            self._proto_cb[emews.base.enums.net_protocols.NET_AGENT] = nonsupported_hub

        # The following servers run on all nodes:
        self._proto_cb[emews.base.enums.net_protocols.NET_SPAWN] = \
            emews.base.serv_spawner.ServSpawner(thread_dispatcher, _inject=inject_par)

    def handle_init(self, session_id, int_addr):
        """Init tasks."""
        session_data = NetCache.SessionData()
        session_data.addr = int_addr
        self._net_cache.session[session_id] = session_data

    def handle_close(self, session_id):
        """Handle the case when a socket is closed."""
        session_data = self._net_cache.session[session_id]
        if session_data.handler is not None:
            # if no handler, means the session ended before a handler was assigned (and thus called)
            session_data.handler.handle_close(session_id)

        del self._net_cache.session[session_id]

    def handle_connection(self, session_id, chunk):
        """Chunk contains the protocol and node id."""
        try:
            proto_id, node_id = struct.unpack('>HL', chunk)
        except struct.error as ex:
            self.logger.warning("Session id: %d, struct error when unpacking protocol: %s",
                                session_id, ex)
            return None

        session_data = self._net_cache.session[session_id]

        if node_id > 0:
            # a node id of zero refers to an unassigned node or client, so don't track it
            node_data = self._net_cache.node.get(node_id, None)

            if node_data is None:
                if self.sys.is_hub:
                    self.logger.warning(
                        "Session id: %d, unrecognized node id given: %d, from address: %s",
                        session_id, node_id, socket.inet_ntoa(struct.pack(">I", session_data.addr)))
                    return None

                # if not the hub node, assume node id is legit
                # TODO: validate node id with hub node
                node_data = NetCache.NodeData()

            node_data.addr = session_data.addr  # update latest address
            session_data.node_id = node_id      # assign node id associated with this session

        if proto_id > len(self._proto_cb) - 1:
            self.logger.warning(
                "Session id: %d, unrecognized protocol id given: %d, from address: %s",
                session_id, proto_id, socket.inet_ntoa(struct.pack(">I", session_data.addr)))
            return None

        session_data.handler = self._proto_cb[proto_id]  # assign handler for this session
        self.logger.debug("Session id: %d, protocol requested: %d", session_id, proto_id)

        return session_data.handler.handle_init(node_id, session_id)
