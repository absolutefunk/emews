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


class NetManager(object):
    """Classdocs."""

    __slots__ = ('logger', 'sys', '_proto_cb', '_node_addr', '_session_info')

    def __init__(self, sysprop):
        """Constructor."""
        self.logger = emews.base.logger.get_logger()
        self.sys = sysprop

        self._node_addr = {}  # [node_id]: most recent observed address
        self._session_info = []  # [session_id]: [addr, serv_obj]  (temp - session duration)

        # protocol mappings
        self._proto_cb = [None] * emews.base.basenet.NetProto.ENUM_SIZE
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_NONE, NonSupportedInvalid())
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_CC_1, NonSupportedInvalid())
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_CC_2, NonSupportedInvalid())

        inject_sys = {'sys': self.sys}

        if self.sys.is_hub:
            # Hub node runs the following servers:
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_HUB,
                                  emews.base.serv_hub.ServHub(_inject=inject_sys))
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_LOGGING,
                                  emews.base.serv_logging.ServLogging(_inject=inject_sys))
        else:
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_HUB, NonSupportedHub())
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_LOGGING, NonSupportedHub())

        # The following servers run on all nodes:
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_AGENT,
                              emews.base.serv_agent.ServAgent(_inject=inject_sys))

    def handle_init(self, session_id, int_addr):
        """
        Return number of bytes expected (buf) to determine protocol.

        proto (2 bytes) + node_id (4 bytes)
        """
        self._session_info[session_id].append(int_addr)  # index [0]
        return (self._proto_dispatch, 6)

    def handle_close(self, session_id):
        """Handle the case when a socket is closed."""
        session_info = self._session_info[session_id]
        if len(session_info) == 2:
            # if not len = 2, means the session ended before a handler was called
            session_info[1].handle_close(session_id)

        del self._session_info[session_id]

    def _proto_dispatch(self, session_id, chunk):
        """Chunk contains the protocol and node id."""
        try:
            proto_id, node_id = struct.unpack('>HL', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking protocol: %s", ex)
            return None

        if node_id > 0:
            # a node id of zero refers to an unassigned node, so don't track it
            self._node_addr[node_id] = self._session_info[session_id][0]  # most recent known addr

        self._session_info[session_id].append(self._proto_cb[proto_id])
        return self._proto_cb[proto_id].handle_init(node_id, session_id)
