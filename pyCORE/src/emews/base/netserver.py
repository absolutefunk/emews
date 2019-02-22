"""
Multi-connection net server, in which each accepted connection is passed off to a handler method.

Created on Feb 21, 2019
@author: Brian Ricks
"""
import socket

import emews.base.basenet


class NetServer(emews.base.basenet.BaseNet):
    """Classdocs."""

    __slots__ = ('_buf_size', '_handler', '_serv_sock')

    def __init__(self, config, sysprop, handler):
        """Constructor."""
        super(NetServer, self).__init__(sysprop)

        sock_host = config['host']
        sock_port = config['port']

        self._buf_size = config['buf_size']
        self._handler = handler

        # parameter checks
        if sock_host == '':
            self._sys.logger.warning(
                "Host not specified. Listener may bind to any available interface.")
        if sock_port < 1 or sock_port > 65535:
            err_msg = "Port is out of range (must be between 1 and 65535, given: %d)"
            self._sys.logger.error(err_msg, sock_port)
            raise ValueError(err_msg % sock_port)
        if sock_port < 1024:
            self._sys.logger.warning("Port is less than 1024 (given: %d).  "
                                     "Elevated permissions may be needed for binding.", sock_port)

        # initialize listener socket
        try:
            self._serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._serv_sock.setblocking(0)
        except socket.error:
            self._sys.logger.error("Could not instantiate socket.")
            raise

        try:
            self._serv_sock.bind((self._host, self._port))
        except socket.error:
            self._serv_sock.close()
            self._sys.logger.error("Could not bind socket to interface.")
            raise
        try:
            self._serv_sock.listen(5)
        except socket.error:
            self._serv_sock.close()
            self._sys.logger.error("Exception when setting up connection requests.")
            raise

        self._sys.logger.info("Listening on interface %s, port %d", sock_host, sock_port)
        self._sock_list.append(self._serv_sock)

    def readable_socket(self, sock):
        """@Override Given a socket in a readable state, do something with it."""
        if sock is self._serv_sock:
            # accept incoming connection
            try:
                acc_sock, src_addr = sock.accept()
                acc_sock.setblocking(0)
            except socket.error as ex:
                # ignore the exception, but dump the new connection
                self._sys.logger.warning("Socket exception while accepting connection: %s", ex)
                return

            self._sys.logger.debug("Connection established from %s", src_addr)
            self._r_socks.append(acc_sock)
        else:
            # readable socket we are managing
            try:
                chunk = sock.recv(self._buf_size)
            except socket.error:
                self._sys.logger.warning(
                    "Socket error when receiving data, closing socket FD '%d' ...", sock.fileno())
                self._close_socket(sock)
                return

            if not len(chunk):
                # zero length chunk, connection probably closed
                self._sys.logger.debug("Connection closed remotely, closing socket FD '%d' ...",
                                       sock.fileno())
                self._close_socket(sock)
                return

            self._handler.handle_received_data(sock.fileno(), chunk)

    def _close_socket(self, sock):
        """Close the passed socket."""
        self._r_socks.remove(sock)
        sock.shutdown(socket.SHUT_RDWR)
