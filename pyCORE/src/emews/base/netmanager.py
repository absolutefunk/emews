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

    __slots__ = ('logger', 'sys', '_proto_cb', '_pending_ids', '_addr_set', '_node_addrs')

    def __init__(self, sysprop):
        """Constructor."""
        self.logger = emews.base.logger.get_logger()
        self.sys = sysprop

        # protocol mappings
        self._proto_cb = [None] * emews.base.basenet.NetProto.ENUM_SIZE
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_NONE, self._unsupported_invalid)
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_CC_1, self._cc_comm)
        self._proto_cb.insert(emews.base.basenet.NetProto.NET_CC_2, self._cc_comm)
        if self.sys.is_hub:
            inject_sys = {'sys': self.sys}
            # Hub node runs the following servers:
            serv_inst = emews.base.serv_agent.ServAgent(_inject=inject_sys)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_AGENT, serv_inst.handle_init)
            serv_inst = emews.base.serv_hub.ServHub(_inject=inject_sys)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_HUB, serv_inst.handle_init)
            serv_inst = emews.base.serv_logging.ServLogging(_inject=inject_sys)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_LOGGING, serv_inst.handle_init)
        else:
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_AGENT, self._unsupported_nonhub)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_HUB, self._unsupported_nonhub)
            self._proto_cb.insert(emews.base.basenet.NetProto.NET_LOGGING, self._unsupported_nonhub)

        self._pending_ids = {}  # [session_id]: int_addr (temp mapping until node_id recv)
        self._addr_set = set()  # set of addresses seen from previous sessions
        self._node_addrs = {}   # [node_id]: [address list] (Index[0] is default address)

    def handle_init(self, id, int_addr):
        """
        Return number of bytes expected (buf) to determine protocol.  Map address.

        proto (2 bytes) + padding (2 bytes) + node_id (4 bytes)
        """
        if int_addr not in self._addr_set:
            # new address
            self._pending_ids[id] = int_addr
        return (self._proto_dispatch, 8)

    def handle_close(self, id):
        """Handle the case when a socket is closed."""
        # id would only be in the pending_ids map if handle_close() is called before
        # _proto_dispatch() and if the address was new (not seen before)
        self._pending_ids.pop(id, None)

    def _proto_dispatch(self, id, chunk):
        """Chunk contains the protocol.  Dispatch appropriate handler."""
        try:
            proto_id, _, node_id = struct.unpack('>HHL', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking protocol info: %s", ex)
            return None

        p_addr = self._pending_ids.pop(id, None)

        if p_addr is not None:
            # this is new address
            self._addr_set.add(p_addr)
            if node_id not in self._node_addrs:
                # new node id
                self._node_addrs[node_id] = []
                self._node_addrs[node_id].append(p_addr)
            else:
                # an existing node id has multiple IP addresses
                self.logger.warning("Multiple IP addresses for node id '%d' (not supported yet).")
                # append new address anyways (will be supported one day)
                self._node_addrs.append(p_addr)  # this will be a secondary address, ie index > 0

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
