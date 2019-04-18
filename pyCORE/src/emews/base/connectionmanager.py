"""
Manages all backend connections between eMews nodes and the Hub node.

Created on Feb 21, 2019
@author: Brian Ricks
"""
import select
import socket
import struct

import emews.base.baseobject
import emews.base.netserv


class HandlerCB(object):
    """Enumerations for ConnectionManager handler methods."""

    __slots__ = ()

    ENUM_SIZE = 2

    REQUEST_CLOSE = 0
    REQUEST_WRITE = 1


class SockState(object):
    """Enumerations for sock state indices."""

    __slots__ = ()

    ENUM_SIZE = 4

    SOCK_NEXT_CB = 0
    SOCK_EXPECTED_BYTES = 1
    SOCK_BUFFER = 2


class ConnectionManager(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_host', '_port', '_socks', '_listener_sock', '_net_serv', '_pending_ids', '_cb',
                 '_r_socks', '_w_socks', '_e_socks')

    def __init__(self, config):
        """Constructor."""
        super(ConnectionManager, self).__init__()

        self._port = config['port']
        self._host = config['host']
        if self._host is None:
            self._host = ''  # any available interface

        self._socks = {}  # accepted sockets
        self._pending_ids = {}  # FDs (socks) that are pending an established connection
        self._listener_sock = None  # listener socket (will be instantiated on start())

        self._net_serv = emews.base.netserv.NetServ(_inject={'sys': self.sys})

        self._r_socks = []  # list of socket objects to manage for a readable state
        self._w_socks = []  # list of socket objects to manage for a writable state
        self._e_socks = []  # list of socket objects to manage for an exceptional state

        # Handler callbacks
        self._cb = [None] * HandlerCB.ENUM_SIZE
        self._cb.insert(HandlerCB.REQUEST_CLOSE, self._request_close)
        self._cb.insert(HandlerCB.REQUEST_WRITE, self._request_write)

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

        self._e_socks.remove(sock)

        if sock in self._socks:
            self._socks[sock].handle_close()
            del self._socks[sock]

            if sock.fileno() in self._pending_ids:
                # connection could not be established
                del self._pending_ids[sock.fileno()]
                self.logger.debug("Connection not established for FD '%d'.", sock.fileno())

        try:
            sock.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass

        sock.close()

    def start(self):
        """Start the ConnectionManager."""
        # create listener socket for the ConnectionManager
        self._setup_listener(self._host, self._port)

        while not self._interrupted:
            try:
                r_sock_list, w_sock_list, e_sock_list = select.select(
                    self._r_socks, self._w_socks, self._e_socks)
            except select.error:
                if not self._interrupted:
                    self.logger.error("Select error while blocking on managed sockets.")
                    raise
                # if run in the main thread, a KeyboardInterrupt should unblock select
                self.logger.debug("Select interrupted by signal.")
                break

            for w_sock in w_sock_list:
                # writable sockets
                self._writable_socket(w_sock)

            for r_sock in r_sock_list:
                # readable sockets
                self._readable_socket(r_sock)

            for e_sock in e_sock_list:
                # exceptional sockets
                self._exceptional_socket(e_sock)

    def stop(self):
        """Stop the ConnectionManager."""
        self.interrupt()

        # shutdown the listener socket first
        self._close_socket(self._listener_sock)

        for sock in self._socks.keys():
            # shut down all managed sockets
            self._close_socket(sock)

    def _readable_socket(self, sock):
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
            self._e_socks.append(acc_sock)

            # call handle_init(), sock FD as session_id, IPv4 address as int
            self._net_serv.handle_init(
                acc_sock.fileno(), struct.unpack(">I", socket.inet_aton(src_addr[0]))[0])

            sock_state = [None] * SockState.ENUM_SIZE
            sock_state.insert(SockState.SOCK_NEXT_CB, self._net_serv.handle_connection)
            sock_state.insert(SockState.SOCK_EXPECTED_BYTES, 6)
            sock_state.append(SockState.SOCK_BUFFER, "")

            self._socks[acc_sock] = sock_state
        else:
            # readable socket we are managing
            sock_state = self._socks[sock]

            try:
                chunk = sock.recv(sock_state[SockState.SOCK_EXPECTED_BYTES])
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
            elif len(chunk) < sock_state[SockState.SOCK_EXPECTED_BYTES]:
                # num bytes recv is less than what is expected.
                sock_state[SockState.SOCK_EXPECTED_BYTES] = \
                    sock_state[SockState.SOCK_EXPECTED_BYTES] - len(chunk)  # bytes remaining
                sock_state[SockState.SOCK_BUFFER] = sock_state[SockState.SOCK_BUFFER] + chunk
                return

            # received all expected bytes
            chunk = sock_state[SockState.SOCK_BUFFER] + chunk
            sock_state[SockState.SOCK_BUFFER] = ""  # clear cache

            try:
                # read cb: returns (cb, buf) for read mode, (data, (cb, buf)) for write mode
                ret_tup = sock_state[SockState.SOCK_NEXT_CB](sock.fileno(), chunk)
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
                    sock_state[SockState.SOCK_NEXT_CB] = None
                    sock_state[SockState.SOCK_EXPECTED_BYTES] = 0
                else:
                    sock_state[SockState.SOCK_NEXT_CB] = ret_tup[1][0]  # next cb
                    sock_state[SockState.SOCK_EXPECTED_BYTES] = ret_tup[1][1]  # next expected bytes

                sock_state[SockState.SOCK_BUFFER] = ret_tup[0]  # data to be sent

                self._r_socks.remove(sock)
                self._w_socks.append(sock)
            else:
                # read mode
                sock_state[SockState.SOCK_NEXT_CB] = ret_tup[0]  # next cb
                sock_state[SockState.SOCK_EXPECTED_BYTES] = ret_tup[1]  # next expected bytes

    def _writable_socket(self, sock):
        """
        Given a socket in a writable state, do something with it.

        Send whatever data is returned from the socket's associated callback, and
        then switch the socket from being writable to readable.
        """
        sock_state = self._socks[sock]

        bytes_sent = sock.send(sock_state[SockState.SOCK_BUFFER])

        if bytes_sent < len(sock_state[SockState.SOCK_BUFFER]):
            # not all bytes were sent - remove those bytes sent
            sock_state[SockState.SOCK_BUFFER] = sock_state[SockState.SOCK_BUFFER][bytes_sent:]
            return

        # all bytes sent
        sock_state[SockState.SOCK_BUFFER] = ""  # clear cache
        if sock_state[SockState.SOCK_NEXT_CB] is None:
            # close the socket
            self._close_socket(sock)
            return
        else:
            # switch to read mode
            self._w_socks.remove(sock)
            self._r_socks.append(sock)

    def _exceptional_socket(self, sock):
        """Close a sock in such a state."""
        self.logger.debug("Closing socket FD '%d' in exceptional state.", sock.fileno())
        self._close_socket(sock)

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
