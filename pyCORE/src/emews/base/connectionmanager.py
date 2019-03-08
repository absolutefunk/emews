"""
Manages all backend connections between eMews nodes and the MasterNode.

Created on Feb 21, 2019
@author: Brian Ricks
"""
import socket

import emews.base.basenet


class ConnectionManager(emews.base.basenet.BaseNet):
    """Classdocs."""

    __slots__ = ('_host', '_buf_size', '_sock_map')

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
        self._sock_map = {}

        self.add_listener(config['port'])  # add listener socket for daemon listener

    def readable_socket(self, sock):
        """@Override Given a socket in a readable state, do something with it."""
        if sock is serv_sock:
            # accept incoming connection
            try:
                acc_sock, src_addr = sock.accept()
                acc_sock.setblocking(0)
            except socket.error as ex:
                # ignore the exception, but dump the new connection
                self._sys.logger.warning("Socket exception while accepting connection: %s", ex)
                return

            self._sys.logger.debug("Connection established from %s", src_addr)
            self._r_socks.add(acc_sock)
            self._sock_map[acc_sock] = {}  # TODO: some state for the socket here
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

            # handle the chunk
            self._sock_map[sock].handle_read(chunk)

    def writable_socket(self, sock):
        """
        @Override Given a socket in a writable state, do something with it.

        Send whatever data is returned from the socket's associated handle_write() callback, and
        then switch the socket from being writable to readable.
        """
        s_data = self._sock_map[sock].handle_write()

        if s_data is not None:
            sock.send(s_data)

        self._w_socks.remove(sock)
        self._r_socks.add(sock)

    def _close_socket(self, sock):
        """Close the passed socket."""
        del self._sock_map[sock]
        sock.shutdown(socket.SHUT_RDWR)

    def add_listener(self, port):
        """Add a new listener (server socket) to this connection manager."""
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
        except socket.error:
            self._sys.logger.error("Could not instantiate new listener socket.")
            raise

        try:
            serv_sock.bind((self._host, port))
        except socket.error:
            serv_sock.close()
            self._sys.logger.error("Could not bind new listener socket to interface.")
            raise
        try:
            serv_sock.listen(5)
        except socket.error:
            serv_sock.close()
            self._sys.logger.error("New listener socket threw socket.error on listen().")
            raise

        self._sys.logger.info("New listener socket on interface %s, port %d.", self._host, port)
        self._r_socks.add(serv_sock)
