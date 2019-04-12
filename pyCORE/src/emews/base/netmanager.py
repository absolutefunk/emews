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


class NetManager(object):
    """Classdocs."""

    __slots__ = ('logger', 'sys', '_proto_cb', '_node_addr', '_session_addr')

    def __init__(self, sysprop):
        """Constructor."""
        self.logger = emews.base.logger.get_logger()
        self.sys = sysprop

        self._node_addr = {}  # [node_id]: most recent observed address
        self._session_addr = {}  # [session_id]: addr  (temp - session duration)

        # protocol mappings
        self._proto_cb = [None] * emews.base.basenet.NetProto.ENUM_SIZE
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_NONE, self._unsupported_invalid)
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_CC_1, self._cc_comm)
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_CC_2, self._cc_comm)

        inject_sys = {'sys': self.sys}

        if self.sys.is_hub:
            # Hub node runs the following servers:
            serv_inst = emews.base.serv_agent.ServAgent(_inject=inject_sys)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_AGENT, serv_inst.handle_init)
            serv_inst = emews.base.serv_hub.ServHub(_inject=inject_sys)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_HUB, serv_inst.handle_init)
            serv_inst = emews.base.serv_logging.ServLogging(_inject=inject_sys)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_LOGGING, serv_inst.handle_init)
        else:
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_HUB, self._unsupported_nonhub)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_LOGGING, self._unsupported_nonhub)

        # The following servers run on all nodes:
        serv_inst = emews.base.serv_agent.ServAgent(_inject=inject_sys)
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_AGENT, serv_inst.handle_init)

    def handle_init(self, session_id, int_addr):
        """
        Return number of bytes expected (buf) to determine protocol.

        proto (2 bytes) + node_id (4 bytes)
        """
        self._session_addr[session_id] = int_addr
        return (self._proto_dispatch, 6)

    def handle_close(self, session_id):
        """Handle the case when a socket is closed."""
        del self._session_addr[session_id]

    def _proto_dispatch(self, session_id, chunk):
        """Chunk contains the protocol and node id."""
        try:
            proto_id, node_id = struct.unpack('>HL', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking protocol: %s", ex)
            return None

        if node_id > 0:
            # a node id of zero refers to an unassigned node, so don't track it
            self._node_addr[node_id] = self._session_addr[session_id]  # most recent known address

        return self._proto_cb[proto_id](node_id, session_id)

    # callbacks
    def _unsupported_invalid(self, node_id, session_id):
        """Invalid protocol id (or reserved)."""
        self.logger.warning("Protocol not supported or reserved.")
        return None

    def _unsupported_nonhub(self, node_id, session_id):
        """Future use for cc channels."""
        self.logger.warning("This protocol server not running: this node is not the hub.")
        return None

    def _cc_comm(self, node_id, session_id):
        """Future use for cc channels."""
        self.logger.warning("CC protocols not implemented yet.")
        return None
