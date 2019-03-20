"""
Manages all backend connections between eMews nodes and the MasterNode.

Created on Feb 21, 2019
@author: Brian Ricks
"""
import socket

import emews.base.basenet
import emews.base.handler_netmanager


class HandlerCB(object):
    """Enumerations of return values for handlers."""

    NO_REQUEST = -1
    REQUEST_CLOSE = 0
    REQUEST_WRITEABLE = 1


class ConnectionManager(emews.base.basenet.BaseNet):
    """Classdocs."""

    __slots__ = ('_host', '_buf_size', '_socks', '_serv_socks', '_cb')

    def __init__(self, config, sysprop):
        """Constructor."""
        super(ConnectionManager, self).__init__(sysprop)

        self._host = config['host']
        if self._host is None:
            self._host = ''

        if self._host == '':
            self._sys.logger.warning(
                "Host not specified. Listener may bind to any available interface.")

        self._buf_size = config['buf_size']

        self._socks = {}
        self._serv_socks = {}

        # callback mapping (ret_val for handlers)
        self._cb = []
        self._cb.append(self._close_socket)   # request socket close    [0]
        self._cb.append(self._request_write)  # request socket writable [1]

        # create listener socket for the ConnectionManager
        self.add_listener(config['port'],
                          emews.base.handler_netmanager.HandlerNetManager(self._sys))

    def _close_socket(self, sock):
        """Close the passed socket.  Should not be used on listener sockets."""
        try:
            del self._socks[sock]
        except KeyError:
            self._sys.logger.warning("Closing socket that is not managed.  "
                                     "Is this a listener socket?")

        sock.shutdown(socket.SHUT_RDWR)

    def _request_write(self, sock):
        """Request passed socket as writable."""
        self._r_socks.remove(sock)
        self._w_socks.append(sock)

    def stop(self):
        """Stop the ConnectionManager."""
        self.interrupt()

        for sock in self._serv_socks.keys():
            self._close_socket(sock)
        for sock in self._socks.keys():
            self._close_socket(sock)

    def readable_socket(self, sock):
        """Given a socket in a readable state, do something with it."""
        if sock in self._serv_socks:
            # listener socket, accept incoming connection
            try:
                acc_sock, src_addr = sock.accept()
                acc_sock.setblocking(0)
            except socket.error as ex:
                # ignore the exception, but dump the new connection
                self._sys.logger.warning("Socket exception while accepting connection: %s", ex)
                return

            self._sys.logger.debug("Connection established from %s", src_addr)
            self._r_socks.append(acc_sock)
            self._socks[acc_sock] = []
            self._socks[acc_sock].append(self._serv_socks[sock])  # handler used [0]
            self._socks[acc_sock].append({})  # state [1]

            self._socks[acc_sock][0].handle_init(self._socks[acc_sock][1])
        else:
            # readable socket we are managing
            try:
                chunk = sock.recv(self._buf_size)
            except socket.error:
                self._sys.logger.warning(
                    "Socket error when receiving data, closing socket FD '%d' ...", sock.fileno())
                self._r_socks.remove(sock)
                self._close_socket(sock)
                return

            if not len(chunk):
                # zero length chunk, connection probably closed
                self._sys.logger.debug("Connection closed remotely, closing socket FD '%d' ...",
                                       sock.fileno())
                self._r_socks.remove(sock)
                self._close_socket(sock)
                return

            # handle the chunk (size > 0)
            ret_val = self._socks[sock][0].handle_read(chunk, self._socks[sock][1])
            if ret_val != HandlerCB.NO_REQUEST:
                # post processing
                self._cb[ret_val](sock)

    def writable_socket(self, sock):
        """
        Given a socket in a writable state, do something with it.

        Send whatever data is returned from the socket's associated handle_write() callback, and
        then switch the socket from being writable to readable.
        """
        s_data = self._socks[sock].handle_write()

        if s_data is not None:
            sock.send(s_data)

        self._w_socks.remove(sock)
        self._r_socks.append(sock)

    def add_listener(self, port, handler):
        """Add a new listener (server socket) to manage."""
        # parameter checks
        if port < 1 or port > 65535:
            err_msg = "Port is out of range (must be between 1 and 65535, given: %d)"
            self._sys.logger.error(err_msg, port)
            raise ValueError(err_msg % port)
        if port < 1024:
            self._sys.logger.warning("Port is less than 1024 (given: %d).  "
                                     "Elevated permissions may be needed for binding.", port)

        # initialize listener socket
        try:
            serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serv_sock.setblocking(0)
        except socket.error as ex:
            self._sys.logger.error("Could not instantiate new listener socket: %s", ex)
            raise

        try:
            serv_sock.bind((self._host, port))
        except socket.error as ex:
            serv_sock.shutdown(socket.SHUT_RDWR)
            self._sys.logger.error("Could not bind new listener socket to interface: %s", ex)
            raise
        try:
            serv_sock.listen(5)
        except socket.error as ex:
            serv_sock.shutdown(socket.SHUT_RDWR)
            self._sys.logger.error("New listener socket threw socket.error on listen(): %s", ex)
            raise

        self._sys.logger.info("New listener socket on interface %s, port %d.", self._host, port)
        self._r_socks.append(serv_sock)
        self._serv_socks[serv_sock] = handler
