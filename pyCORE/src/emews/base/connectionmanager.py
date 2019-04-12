"""
Manages all backend connections between eMews nodes and the Hub node.

Created on Feb 21, 2019
@author: Brian Ricks
"""
import socket
import struct

import emews.base.basenet
import emews.base.netmanager


class ConnectionManager(emews.base.basenet.BaseNet):
    """Classdocs."""

    __slots__ = ('sys', '_host', '_port', '_socks', '_listener_sock', '_net_manager',
                 '_pending_ids', '_cb',)

    def __init__(self, config, sysprop):
        """Constructor."""
        self.sys = sysprop

        self._port = config['port']
        self._host = config['host']
        if self._host is None:
            self._host = ''  # any available interface

        self._socks = {}  # accepted sockets
        self._pending_ids = {}  # FDs (socks) that are pending an established connection
        self._listener_sock = None  # listener socket (will be instantiated on start())
        self._net_manager = emews.base.netmanager.NetManager(self.sys)

        # Handler callbacks
        self._cb = [None] * emews.base.basenet.HandlerCB.ENUM_SIZE
        self._cb.insert(emews.base.basenet.HandlerCB.REQUEST_CLOSE, self._request_close)
        self._cb.insert(emews.base.basenet.HandlerCB.REQUEST_WRITE, self._request_write)

    def _close_socket(self, sock):
        """Close the passed socket.  Should not be used on listener sockets."""
        try:
            self._w_socks.remove(sock)
        except ValueError:
            pass

        try:
            self._r_socks.remove(sock)
        except ValueError:
            pass

        if sock in self._socks:
            self._socks[sock].handle_close()
            del self._socks[sock]

            if sock.fileno() in self._pending_ids:
                # connection could not be established
                del self._pending_ids[sock.fileno()]
                self.logger.debug("Connection refused from remote for FD '%d'.", sock.fileno())

        sock.shutdown(socket.SHUT_RDWR)

    def start(self):
        """Start the ConnectionManager."""
        # create listener socket for the ConnectionManager
        self._setup_listener(self._host, self._port)

        super(ConnectionManager, self).start()

    def stop(self):
        """Stop the ConnectionManager."""
        self.interrupt()

        self._close_socket(self._listener_sock)
        for sock in self._socks.keys():
            self._close_socket(sock)

    def readable_socket(self, sock):
        """Given a socket in a readable state, do something with it."""
        if sock is self._listener_sock:
            # listener socket, accept incoming connection
            try:
                acc_sock, src_addr = sock.accept()
                acc_sock.setblocking(0)
            except socket.error as ex:
                # ignore the exception, but dump the new connection
                self.logger.warning("Socket exception while accepting connection: %s", ex)
                return

            self.logger.debug("Connection established from %s", src_addr)
            self._r_socks.append(acc_sock)

            sock_state = []
            sock_state.append(self._net_manager.handle_init)  # current handler cb [0]
            sock_state.append(0)  # expected number of bytes to receive next (buf) [1]
            sock_state.append("")  # cache [2]

            # call handle_init(), sock FD as session_id, IPv4 address as int
            sock_state[0](acc_sock.fileno(), struct.unpack(">I", socket.inet_aton(src_addr[0]))[0])
            self._socks[acc_sock] = sock_state
        else:
            # readable socket we are managing
            sock_state = self._socks[sock]

            try:
                chunk = sock.recv(sock_state[1])  # recv at most the current buf size
            except socket.error:
                self.logger.warning(
                    "Socket error when receiving data, closing socket FD '%d' ...", sock.fileno())
                self._close_socket(sock)
                return

            if not len(chunk):
                # zero length chunk, connection probably closed
                self.logger.debug("Connection closed remotely, closing socket FD '%d' ...",
                                  sock.fileno())
                self._close_socket(sock)
            elif len(chunk) < sock_state[1]:
                # num bytes recv is less than what is expected.
                sock_state[1] = sock_state[1] - len(chunk)  # bytes remaining
                sock_state[2] = sock_state[2] + chunk
                return

            # received all expected bytes
            if sock_state[2] is not None:
                chunk = sock_state[2] + chunk
                sock_state[2] = ""  # clear cache

            try:
                # read cb: returns (cb, buf) for read mode, (data, (cb, buf)) for write mode
                ret_tup = sock_state[0](sock.fileno(), chunk)
            except TypeError:
                self.logger.error("Handler callback is not callable.")
                raise

            if ret_tup is None:
                # close the socket
                self._close_socket(sock)
            elif isinstance(ret_tup[1], tuple):
                # write mode
                if ret_tup[1] is None:
                    # close the socket after write
                    sock_state[0] = None
                    sock_state[1] = 0
                else:
                    sock_state[0] = ret_tup[1][0]  # next cb
                    sock_state[1] = ret_tup[1][1]  # next expected bytes

                sock_state[2] = ret_tup[0]  # data to be sent

                self._r_socks.remove(sock)
                self._w_socks.append(sock)
            else:
                # read mode
                sock_state[0] = ret_tup[0]  # next cb
                sock_state[1] = ret_tup[1]  # next expected bytes

    def writable_socket(self, sock):
        """
        Given a socket in a writable state, do something with it.

        Send whatever data is returned from the socket's associated callback, and
        then switch the socket from being writable to readable.
        """
        sock_state = self._socks[sock]

        bytes_sent = sock.send(sock_state[2])

        if bytes_sent < len(sock_state[2]):
            # not all bytes were sent
            sock_state[2] = sock_state[2][bytes_sent:]  # remove the chars already sent
            return

        # all bytes sent
        sock_state[2] = ""  # clear cache
        if sock_state[0] is None:
            # close the socket
            self._close_socket(sock)
            return
        else:
            # switch to read mode
            self._w_socks.remove(sock)
            self._r_socks.append(sock)

    def _setup_listener(self, host, port):
        """Create listener (server socket) to manage."""
        # parameter checks
        if port < 1 or port > 65535:
            raise ValueError("Port is out of range (must be between 1 and 65535, given: %d)" % port)
        if port < 1024:
            self.logger.warning("Port is less than 1024 (given: %d).  "
                                "Elevated permissions may be needed for binding.", port)

        # initialize listener socket
        try:
            serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serv_sock.setblocking(0)
        except socket.error as ex:
            self.logger.error("Could not instantiate new listener socket: %s", ex)
            raise

        try:
            serv_sock.bind((host, port))
        except socket.error as ex:
            serv_sock.shutdown(socket.SHUT_RDWR)
            self.logger.error("Could not bind new listener socket to interface: %s", ex)
            raise
        try:
            serv_sock.listen(5)
        except socket.error as ex:
            serv_sock.shutdown(socket.SHUT_RDWR)
            self.logger.error("New listener socket threw socket.error on listen(): %s", ex)
            raise

        self.logger.info("New listener socket on interface %s, port %d.", self._host, port)

        self._r_socks.append(serv_sock)
        self._listener_sock = serv_sock

    def connect_node(self, node_name, callback_obj):
        """
        Establish a connection using the passed node name.

        callback_obj is the callback object to use once connected.
        """
        try:
            cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cli_sock.setblocking(0)
        except socket.error as ex:
            self.logger.error("Could not instantiate new client socket: %s", ex)
            raise

        conn_addr = self.sys.get_addr_from_name(node_name)  # TODO: no more function in sys
        cli_sock.connect_ex((conn_addr, self._port))  # use the default eMews daemon port

        sock_lst = []
        sock_lst.append(self._cli_conn_ack)  # current handler cb [0]
        sock_lst.append(1)  # expected number of bytes to receive next (buf) [1]
        sock_lst.append(None)  # recv cache [2]
        self._socks[cli_sock] = sock_lst

        self._pending_ids[cli_sock.fileno()] = callback_obj

        self._r_socks.append(cli_sock)  # wait until we receive an ack from the receiving node

    def _cli_conn_ack(self, id, chunk):
        """Acknowledgment from remote when successful connection."""
        try:
            recv_state = struct.unpack('>H', chunk)
        except struct.error as ex:
            self.logger.warning("Struct error when unpacking protocol info: %s", ex)
            return None

        if recv_state != emews.base.basenet.HandlerCB.STATE_ACK:
            # invalid response
            self.logger.warning("Invalid response from remote for FD '%d'.", id)
            return None

        handler_obj = self._pending_ids.pop(id)
        handler_obj.set_request_write(self._request_write)
        return handler_obj.handle_init(id)  # return next cb
