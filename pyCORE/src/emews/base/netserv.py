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

        __slots__ = ('addr', 'node_id', 'serv', 'handler', 'recv_type_str', 'recv_args',
                     'recv_index')

        def __init__(self):
            """Constructor."""
            self.addr = None         # network address of this session
            self.node_id = None      # node id associated with this session
            self.serv = None         # server handling this session
            self.handler = None      # current recv data handler
            self.recv_type_str = ''  # current recv type string (struct unpack)
            self.recv_args = []      # current list of args received and unpacked
            self.recv_index = 0      # current index in handler for expected recv bytes / type str

    __slots__ = ('node', 'session')

    def __init__(self):
        """Constructor."""
        self.node = {}    # [node_id]: NodeData
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

        # build net protocols (must be called before instantiation)
        emews.base.serv_hub.ServHub.build_protocols()
        emews.base.serv_agent.ServAgent.build_protocols()
        emews.base.serv_spawner.ServSpawner.build_protocols()

        if self.sys.is_hub:
            # Hub node runs the following servers:
            self._proto_cb[emews.base.enums.net_protocols.NET_HUB] = \
                emews.base.serv_hub.ServHub(_inject=inject_par)
            self._proto_cb[emews.base.enums.net_protocols.NET_LOGGING] = \
                emews.base.serv_logging.ServLogging(_inject=inject_par)
            self._proto_cb[emews.base.enums.net_protocols.NET_AGENT] = \
                emews.base.serv_agent.ServAgent(thread_dispatcher, _inject=inject_par)
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
        if session_data.serv is not None:
            # if no handler, means the session ended before a handler was assigned (and thus called)
            session_data.serv.handle_close(session_id)

        del self._net_cache.session[session_id]

    def handle_connection(self, session_id, chunk):
        """Chunk contains the protocol and node id."""
        try:
            proto_id, node_id = struct.unpack('>HL', chunk)
        except struct.error as ex:
            self.logger.warning("Session id: %d, struct error when unpacking protocol: %s",
                                session_id, ex)
            return (None, 0)

        session_data = self._net_cache.session[session_id]

        if node_id > 0:
            # a node id of zero refers to an unassigned node or client, so don't track it
            node_data = self._net_cache.node.get(node_id, None)

            if node_data is None:
                if self.sys.is_hub:
                    self.logger.warning(
                        "Session id: %d, unrecognized node id given: %d, from address: %s",
                        session_id, node_id, socket.inet_ntoa(struct.pack(">I", session_data.addr)))
                    return (None, 0)

                # if not the hub node, assume node id is legit
                # TODO: validate node id with hub node
                node_data = NetCache.NodeData()

            node_data.addr = session_data.addr  # update latest address
            session_data.node_id = node_id      # assign node id associated with this session

        if proto_id > len(self._proto_cb) - 1:
            self.logger.warning(
                "Session id: %d, unrecognized protocol id given: %d, from address: %s",
                session_id, proto_id, socket.inet_ntoa(struct.pack(">I", session_data.addr)))
            return (None, 0)

        session_data.serv = self._proto_cb[proto_id]
        self.logger.debug("Session id: %d, protocol requested: %d", session_id, proto_id)

        return self._new_handler_invocation(
            session_id, session_data.serv.handle_init(node_id, session_id))

    def _handle_data(self, session_id, chunk):
        """Handle chunk during a session with a serv."""
        # connection manager expects: (cb, buf) for read mode, (cb, buf, data) for write mode
        session_data = self._net_cache.session[session_id]
        handler = session_data.handler

        try:
            var_tup = struct.unpack(session_data.recv_type_str, chunk)
        except struct.error as ex:
            self.logger.warning("Session id: %d, struct error when unpacking chunk: %s",
                                session_id, ex)
            return (None, 0)

        if session_data.recv_index == len(handler.recv_types) - 1:
            # no more data to recv, invoke callback
            session_data.recv_args.extend(var_tup)
            return self._invoke_handler(session_id, handler)

        session_data.recv_index += 1

        # return the next expected bytes to receive
        recv_str = handler.recv_types[session_data.recv_index][0]
        if recv_str == 's':
            session_data.recv_args.extend(var_tup[:-1])  # don't append last val, as it's the s len

            # prepare for string reception
            s_len = var_tup[-1]

            if s_len > 0:
                session_data.recv_type_str = '>%ds' % var_tup[-1]
                next_recv_bytes = s_len  # next recv bytes correspond to s len
            else:
                self.logger.debug(
                    "Session id: %d, received zero len string, appending empty string ...",
                    session_id)

                session_data.recv_args.append('')
                session_data.recv_index += 1  # skip the string recv_str (None var appended)

                if session_data.recv_index == len(handler.recv_types):
                    # no more data to recv, invoke callback
                    # comparison here is to the recv_list len, as we increment recv_index by 2
                    return self._invoke_handler(session_id, handler)

                session_data.recv_type_str = handler.recv_types[session_data.recv_index][0]
                next_recv_bytes = handler.recv_types[session_data.recv_index][1]  # next recv bytes

        else:
            session_data.recv_type_str = recv_str
            session_data.recv_args.extend(var_tup)
            next_recv_bytes = handler.recv_types[session_data.recv_index][1]  # next recv bytes

        return (self._handle_data, next_recv_bytes)

    def _new_handler_invocation(self, session_id, handler):
        """Invoke new handler."""
        session_data = self._net_cache.session[session_id]
        session_data.recv_index = 0
        session_data.recv_type_str = ''
        session_data.recv_args = []

        session_data.handler = handler

        if not len(handler.recv_types):
            self.logger.debug(
                "Session id: %d, handler doesn't require received data, invoking immediately ...",
                session_id)
            return self._invoke_handler(session_id, handler)

        session_data.recv_type_str = handler.recv_types[0][0]
        return (self._handle_data, handler.recv_types[0][1])

    def _invoke_handler(self, session_id, handler):
        """Invoke the handler callback once all data has been received."""
        session_data = self._net_cache.session[session_id]
        ret_val = handler.callback(session_id, *session_data.recv_args)

        # handle return types
        if ret_val is None:
            # end the session
            return (None, 0)
        elif (isinstance(ret_val, tuple)):
            # send some data
            if handler.protocol.return_type is None or handler.protocol.return_type == '':
                self.logger.warning(
                    "Session id: %d, type specified to pack string is empty.", session_id)
                return (None, 0)

            if handler.protocol.return_type == 's':
                # string return type - len needs to be part of this
                send_data = struct.pack('>H%ss' % len(ret_val[0]), len(ret_val[0]), ret_val[0])
            else:
                send_data = struct.pack('>%s' % handler.protocol.return_type, ret_val[0])

            if ret_val[1] is None:
                # send some data and then end the session.
                return (None, 0, send_data)

            # send some data and invoke new handler
            inv_tup = self._new_handler_invocation(session_id, ret_val[1])
            return (inv_tup[0], inv_tup[1], send_data)

        # new handler (keep same session)
        return self._new_handler_invocation(session_id, ret_val)
