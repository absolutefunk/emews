"""
Network client functionality.

Created on Apr 17, 2019
@author: Brian Ricks
"""
import socket
import struct

import emews.base.baseclient
import emews.base.baseobject
import emews.base.baseserv
import emews.base.enums

"""
TODO: Refactor this to only use a single connection to the hub node.  So instead of multiple
connections to the hub per node, we establish a single connection, and keep it persistent
throughout an experimental run.  This would have the additional benefit of freeing 'None' for use
to return (ie, if something being looked up doesn't exist).
"""


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
                 '_session_id', 'hub_query', '_client_sessions', 'protocols')

    def __init__(self, config, hub_addr):
        """Constructor."""
        super(NetClient, self).__init__()

        self._port = config['port']
        self._hub_addr = hub_addr

        self._conn_timeout = config['connect_timeout']
        self._conn_max_attempts = config['connect_max_attempts']

        self._num_clients = 0  # unique id given to client object instances

        self._client_sessions = {}  # sock management for client sessions
        self._session_id = 1  # sock session id (note, different than ConnectionManager session ids)

        self.protocols = emews.base.baseserv.BaseServ.protocols

        # method pointers (allows monkey-patching)
        self.hub_query = self._hub_query

    def _sock_connect(self, addr=None):
        """Connect to addr, return a (socket, dest_addr)."""
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
            sock.close()
            err_msg = "Exhausted attempts trying to connect to node at address %s." % str(conn_addr)
            self.logger.error(err_msg)
            raise IOError(err_msg)

        return (sock, conn_addr)

    def _client_session_reconnect(self, session_id):
        """Attempt to reconnect a failed connection."""
        if session_id not in self._client_sessions:
            err_msg = "Session id '%d' does not exist" % session_id
            self.logger.error(err_msg)
            raise AttributeError(err_msg)

        _, addr, serv_proto = self._client_sessions[session_id]

        sock = self._sock_connect(addr)[0]

        self._client_sessions[session_id] = (sock, addr)

        self.logger.info(
            "Client-side session id %d: connection re-established to node address '%s'",
            session_id, str(addr))

        try:
            sock.sendall(struct.pack(">HL", serv_proto, self.sys.node_id))
        except socket.error as ex:
            self.logger.warning(
                "Client-side session id %d: connection issue on reconnect (serv protocol send): %s",
                session_id, ex)
            sock.close()
            raise

    def _get_client_instance(self, class_def, *args):
        """Return an inject dict for new net clients."""
        inject_dict = {}
        inject_dict['sys'] = self.sys
        inject_dict['_client_name'] = class_def.__name__ + str(self._num_clients)
        inject_dict['_conn_timeout'] = self._conn_timeout
        inject_dict['_conn_max_attempts'] = self._conn_max_attempts

        self._num_clients += 1

        return class_def(*args, _inject=inject_dict)

    def _hub_query(self, request_id):
        """
        Given a request, return the corresponding result.

        Note that this is a client-side (blocking) operation.
        """
        session_id = self.create_client_session()
        protocol = self.protocols[emews.base.enums.net_protocols.NET_HUB][request_id]

        result = self.node_query(session_id, protocol)

        self.close_connection(session_id)
        return result

    def close_all_sockets(self):
        """Close all managed sockets (self._sock_state)."""
        for sock, _ in self._client_sessions.values():
            sock.close()

    def close_connection(self, session_id):
        """Close the connection of the passed sock."""
        if session_id not in self._client_sessions:
            err_msg = "Session id '%d' does not exist" % session_id
            self.logger.error(err_msg)
            raise AttributeError(err_msg)

        sock = self._client_sessions[session_id][0]

        del self._client_sessions[session_id]

        try:
            sock.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass

        sock.close()

    def node_query(self, session_id, protocol, val_list=[]):
        """
        Query a node, using an existing session, and return the result.

        protocol: specific protocol on the server (server is established on session connection)
        val_list: values to send (types specified in the protocol)
        """
        if session_id not in self._client_sessions:
            err_msg = "Session id '%d' does not exist" % session_id
            self.logger.error(err_msg)
            raise AttributeError(err_msg)

        sock = self._client_sessions[session_id][0]

        try:
            send_vals = [protocol.request_id]
            send_vals.extend(val_list)
            sock.sendall(struct.pack('>H%s' % protocol.format_string, *send_vals))
        except socket.error as ex:
            self.logger.warning(
                "Client-side session id %d: connection issue (query command send): %s",
                session_id, ex)
            sock.close()
            raise

        # receive result
        if protocol.return_type == 's':
            # we don't know the length of the string, but we will get the length first
            buf_len = 2
            str_len_recv = True
        else:
            buf_len = emews.base.baseserv.calculate_recv_len(protocol.return_type)
            str_len_recv = False

        bytes_recv = ''
        while not self._interrupted and len(bytes_recv) < buf_len:
            try:
                # If a signal is caught to shutdown, but the socket does not catch it (say because
                # it is running from another thread than the main one), the hub node will catch it
                # and close the socket from its side, unblocking it here.
                chunk = sock.recv(buf_len)  # query result (4 bytes)

            except socket.error as ex:
                self.logger.warning(
                    "Client-side session id %d: connection issue (query result receive): %s",
                    session_id, ex)
                sock.close()
                raise

            if not len(chunk):
                warn_msg = "Client-side session id %d: connection closed remotely." % session_id
                self.logger.warning(warn_msg)
                sock.close()
                raise socket.error(warn_msg)

            bytes_recv += chunk

            if str_len_recv and len(bytes_recv) == buf_len:
                # we've received the length of the incoming string
                str_len_recv = False

                try:
                    buf_len = struct.unpack('>H', bytes_recv)[0]
                except struct.error as ex:
                    self.logger.warning(
                        "Client-side session id %d: unexpected data format (str len) from: %s",
                        session_id, ex)
                    return None

                self.logger.debug("Client-side session id %d: incoming string of len: %d",
                                  session_id, buf_len)
                bytes_recv = ''

        try:
            if protocol.return_type == 's':
                result = struct.unpack('>%ss' % len(bytes_recv), bytes_recv)[0]
            else:
                result = struct.unpack('>%s' % protocol.return_type, bytes_recv)[0]
        except struct.error as ex:
            self.logger.warning("Client-side session id %d: unexpected data format from: %s",
                                session_id, ex)
            return None

        return result

    # client session methods - client sessions are persistent, and their session ids remain static
    def create_client_session(self, serv_proto, addr=None):
        """
        Attempt to make a connection to the node given by address.

        Note that this is a client-side (blocking) operation.  Currently client sessions are bound
        to a specific server protocol.  This is due to legacy design choices back when server
        connections were for single requests.
        """
        sock, dest_addr = self._sock_connect(addr)

        if self._interrupted:
            return None

        session_id = self._session_id
        self._session_id += 1
        self._client_sessions[session_id] = (sock, dest_addr, serv_proto)

        self.logger.info(
            "Client-side session id %d: New connection established to node address '%s'",
            session_id, str(dest_addr))

        try:
            sock.sendall(struct.pack(">HL", serv_proto, self.sys.node_id))
        except socket.error as ex:
            self.logger.warning(
                "Client-side session id %d: connection issue (serv protocol send): %s",
                session_id, ex)
            sock.close()
            raise

        return session_id

    def _client_session_query(self, session_id, protocol, val_list):
        """Get a value (type is return_type), based on protocol and byte string to send."""
        if self._interrupted:
            return None

        while not self._interrupted:
            try:
                result = self.node_query(session_id, protocol, val_list=val_list)
            except socket.error:
                # attempt to reconnect and try again (if reconnect fails, exception raised)
                self._client_session_reconnect(session_id)
                continue

            break

        return result

    def client_session_get(self, session_id, protocol, val_list):
        """Put data somewhere, based on protocol and byte string to send."""
        return self._client_session_query(session_id, protocol, val_list)

    def client_session_put(self, session_id, protocol, val_list):
        """Put data somewhere, based on protocol and byte string to send."""
        return self._client_session_query(session_id, protocol, val_list)

    # clients which need to run in a thread - these methods return an object suitable for dispatch
    def broadcast_message(self, message, interval, duration):
        """Broadcast a message using the given interval, over the given duration."""
        return self._get_client_instance(BroadcastMessage, self._port, message, interval, duration)
