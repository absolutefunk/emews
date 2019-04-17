"""
Network handler for node to node communication.

Created on March 20, 2019
@author: Brian Ricks
"""
import struct

import emews.base.basenet
import emews.base.logger
import emews.base.serv_agent
import emews.base.serv_hub
import emews.base.serv_logging


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


class NetServ(object):
    """Classdocs."""

    __slots__ = ('logger', 'sys', '_proto_cb', '_net_cache')

    def __init__(self, sysprop):
        """Constructor."""
        self.logger = emews.base.logger.get_logger()
        self.sys = sysprop

        self._net_cache = NetCache()  # net cache shared among the servers

        # protocol mappings
        self._proto_cb = [None] * emews.base.basenet.NetProto.ENUM_SIZE
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_NONE, NonSupportedInvalid())
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_CC_1, NonSupportedInvalid())
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_CC_2, NonSupportedInvalid())

        inject_par = {'logger': self.logger, 'sys': self.sys, 'net_cache': self._net_cache}

        if self.sys.is_hub:
            # Hub node runs the following servers:
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_HUB,
                                  emews.base.serv_hub.ServHub(_inject=inject_par))
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_LOGGING,
                                  emews.base.serv_logging.ServLogging(_inject=inject_par))
        else:
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_HUB, NonSupportedHub())
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_LOGGING, NonSupportedHub())

        # The following servers run on all nodes:
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_AGENT,
                              emews.base.serv_agent.ServAgent(_inject=inject_par))

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
            self.logger.warning("Struct error when unpacking protocol: %s", ex)
            return None

        session_data = self._net_cache.session[session_id]

        if node_id > 0:
            # a node id of zero refers to an unassigned node, so don't track it
            node_data = self._net_cache.node.get(node_id, None)

            if node_data is None:
                if self.sys.is_hub:
                    self.logger.warning("Unrecognized node id given: %d, from address: %d",
                                        node_id, session_data.addr)
                    return None

                # if not the hub node, assume node id is legit
                # TODO: validate node id with hub node
                node_data = NetCache.NodeData()

            node_data.addr = session_data.addr  # update latest address
            session_data.node_id = node_id      # assign node id associated with this session

        session_data.handler = self._proto_cb[proto_id]  # assign handler for this session

        return session_data.handler.handle_init(node_id, session_id)
