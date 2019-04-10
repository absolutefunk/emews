"""
Network handler for node to node communication.

Created on March 20, 2019
@author: Brian Ricks
"""
import struct

import emews.base.basehandler
import emews.base.basenet
import emews.base.serv_agent
import emews.base.serv_hub


class HandlerNetManager(emews.base.basehandler.BaseHandler):
    """Classdocs."""

    __slots__ = ('_proto_cb')

    def __init__(self):
        """Constructor."""
        super(HandlerNetManager, self).__init__()

        p_inj = {
            '_sys': self.sys,
            'logger': self.logger
        }
        # protocol mappings
        self._proto_cb = [None] * emews.base.basenet.NetProto.ENUM_SIZE
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_NONE, self._unsupported_invalid)
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_CC_1, self._cc_comm)
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_CC_2, self._cc_comm)
        if self.sys.is_hub:
            # Hub node runs the following servers:
            serv_inst = emews.base.serv_agent.ServAgent(_inject=p_inj)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_AGENT, serv_inst.handle_init)
            serv_inst = emews.base.serv_hub.ServHub(_inject=p_inj)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_HUB, serv_inst.handle_init)
        else:
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_AGENT, self._unsupported_nonhub)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_HUB, self._unsupported_nonhub)

    def handle_init(self, id, int_addr):
        """
        Return number of bytes expected (buf) to determine protocol.

        proto (2 bytes) + padding (2 bytes) + node_id (4 bytes)
        """
        return (self._proto_dispatch, 8)

    def handle_close(self, id):
        """Handle the case when a socket is closed."""
        pass

    def _proto_dispatch(self, id, chunk):
        """Chunk contains the protocol.  Dispatch appropriate handler."""
        try:
            proto_id, _, node_id = struct.unpack('>HHL', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking protocol info: %s", ex)
            return None

        return self._proto_cb[proto_id](id, node_id)

    # callbacks
    def _unsupported_invalid(self, id, chunk):
        """Invalid protocol id (or reserved)."""
        self.logger.warning("Protocol not supported or reserved.")
        return None

    def _unsupported_nonhub(self, id, chunk):
        """Future use for cc channels."""
        self.logger.warning("This protocol server not running: this node is not the hub.")
        return None

    def _cc_comm(self, id, chunk):
        """Future use for cc channels."""
        self.logger.warning("CC protocols not implemented yet.")
        return None
