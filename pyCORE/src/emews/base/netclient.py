"""
Network client functionality.

Created on Apr 17, 2019
@author: Brian Ricks
"""
import socket
import struct

import emews.base.baseclient
import emews.base.baseobject
import emews.base.enums


# client classes - these run in separate threads and are suitable for ThreadDispatcher dispatch
class BroadcastMessage(emews.base.baseclient.BaseClient):
    """Broadcasts a message across the network."""

    __slots__ = ('_port', '_message', '_interval', '_duration', '_sock')

    def __init__(self, port, message, interval, duration):
        """Constructor."""
        super(BroadcastMessage, self).__init__()

        self._port = port
        self._message = message
        self._interval = interval
        self._duration = duration
        self._sock = None

    def run_client(self):
        """Run the broadcast."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        elapsed_time = 0

        # not the most precise way of time keeping, but good enough
        while elapsed_time < self._duration and not self._interrupted:
            self.sleep(self._interval)
            elapsed_time += self._interval
            try:
                self._sock.sendto(self._message, ('255.255.255.255', self._port))
            except socket.error:
                continue

        self._sock.close()
        self._sock = None
        self.logger.debug("%s: Broadcast finished.", self._client_name)


class NetClient(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_port', '_hub_addr', '_conn_timeout', '_conn_max_attempts', '_num_clients',
                 '_sock_state', '_session_id', 'hub_query')

    def __init__(self, config, hub_addr):
        """Constructor."""
        super(NetClient, self).__init__()

        self._port = config['port']
        self._hub_addr = hub_addr

        self._conn_timeout = config['connect_timeout']
        self._conn_max_attempts = config['connect_max_attempts']

        self._num_clients = 0  # unique id given to client object instances

        self._sock_state = {}  # sock management for NetClient sockets
        self._session_id = 1  # sock session id (note, different than ConnectionManager session ids)

        # method pointers (allows monkey-patching)
        self.hub_query = self._hub_query

    def close_all_sockets(self):
        """Close all managed sockets (self._sock_state)."""
        for sock in self._sock_state.values():
            sock.close()

    def connect_node(self, addr=None):
        """
        Attempt to make a connection to the node given by address.

        Note that this is a client-side (blocking) operation.
        """
        connect_attempts = 0
        conn_addr = addr if addr is not None else self._hub_addr

        while not self._interrupted and connect_attempts < self._conn_max_attempts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self._conn_timeout)
                sock.connect((conn_addr, self._port))
            except socket.error as ex:
                sock.close()
                connect_attempts += 1
                self.logger.debug(
                    "Connection attempt %d failed to connect to node at address %s: %s",
                    connect_attempts, str(conn_addr), ex)
                continue

            break  # forgetting this results in some nice flooding action

        if self._interrupted:
            return None

        if connect_attempts == self._conn_max_attempts:
            # query failed
            self.logger.warning("Exhausted attempts trying to connect to node at address %s.",
                                str(conn_addr))
            return None

        session_id = self._session_id
        self._session_id += 1
        self._sock_state[session_id] = sock

        self.logger.debug(
            "New connection established to node address '%s', assigned client-side session id: %d",
            str(conn_addr), session_id)

        return session_id

    def close_connection(self, session_id):
        """Close the connection of the passed sock."""
        sock = self._sock_state.get(session_id, None)
        if sock is None:
            return

        del self._sock_state[session_id]

        try:
            sock.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass

        sock.close()

    def node_query(self, session_id, proto, query_type_str, query_commands, return_type='L'):
        """
        Query a node, return the result.

        proto = protocol (corresonding server) to handle query
        query_type_str = string of types, each type at index maps to command at index in list
        query_commands = list of commands to send
        """
        sock = self._sock_state.get(session_id, None)

        if self._interrupted or sock is None:
            return None

        try:
            sock.sendall(struct.pack('>HL', proto, self.sys.node_id))
        except socket.error as ex:
            self.logger.warning(
                "Connection issue (protocol send) from session id %d: %s", session_id, ex)
            self.close_connection(session_id)
            return None

        if self._interrupted:
            return None

        # prepare type string
        struct_format = '>'
        for type_chr, cmd in zip(query_type_str, query_commands):
            if type_chr == 's':
                struct_format += 'L' + str(len(cmd)) + 's'  # 4 bytes for str len
            else:
                struct_format += type_chr

        try:
            sock.sendall(struct.pack(struct_format, *query_commands))
        except socket.error as ex:
            self.logger.warning(
                "Connection issue (query command send) from session id %d: %s", session_id, ex)
            self.close_connection(session_id)
            return None

        # receive result
        try:
            # If a signal is caught to shutdown, but the socket does not catch it (say because
            # it is running from another thread than the main one), the hub node will catch it
            # and close the socket from its side, unblocking it here.
            chunk = sock.recv(4)  # query result (4 bytes)

            if self._interrupted:
                return None

            result = struct.unpack('>%s' % return_type, chunk)[0]
        except socket.error as ex:
            self.logger.warning(
                "Connection issue (query result receive) from session id %d: %s", session_id, ex)
            self.close_connection(session_id)
            return None
        except struct.error as ex:
            self.logger.warning("Unexpected data format from session id %d: %s", session_id, ex)
            self.close_connection(session_id)
            return None

        return result

    def _hub_query(self, request):
        """
        Given a request, return the corresponding result.

        Note that this is a client-side (blocking) operation.
        """
        session_id = self.connect_node()

        if session_id is None:
            return None

        result = self.node_query(
            session_id, emews.base.enums.net_protocols.NET_HUB, 'H', [request])

        self.close_connection(session_id)
        return result

    def _get_client_instance(self, class_def, *args):
        """Return an inject dict for new net clients."""
        inject_dict = {}
        inject_dict['sys'] = self.sys
        inject_dict['_client_name'] = class_def.__name__ + str(self._num_clients)
        inject_dict['_conn_timeout'] = self._conn_timeout
        inject_dict['_conn_max_attempts'] = self._conn_max_attempts

        self._num_clients += 1

        return class_def(*args, _inject=inject_dict)

    # clients which need to run in a thread - these methods return an object suitable for dispatch
    def broadcast_message(self, message, interval, duration):
        """Broadcast a message using the given interval, over the given duration."""
        return self._get_client_instance(BroadcastMessage, self._port, message, interval, duration)
