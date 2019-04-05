"""
Manages all backend connections between eMews nodes and the MasterNode.

Created on Feb 21, 2019
@author: Brian Ricks
"""
import socket

import emews.base.basenet
import emews.base.handler_netmanager


class ConnectionManager(emews.base.basenet.BaseNet):
    """Classdocs."""

    __slots__ = ('_host', '_port', '_socks', '_serv_socks', '_cb')

    def __init__(self, config, sysprop):
        """Constructor."""
        super(ConnectionManager, self).__init__(sysprop)

        self._port = config['port']
        self._host = config['host']
        if self._host is None:
            self._host = ''

        if self._host == '':
            self._sys.logger.warning(
                "Host not specified. Listener may bind to any available interface.")

        self._socks = {}
        self._serv_socks = {}

        # Handler callbacks
        self._cb = [None] * emews.base.basenet.HandlerCB.ENUM_SIZE
        self._cb.insert(emews.base.basenet.HandlerCB.REQUEST_CLOSE, self._request_close)
        self._cb.insert(emews.base.basenet.HandlerCB.REQUEST_WRITE, self._request_write)

        # create listener socket for the ConnectionManager
        self.add_listener(self._port, emews.base.handler_netmanager.HandlerNetManager)

    def _close_socket(self, sock):
        """Close the passed socket.  Should not be used on listener sockets."""
        try:
            self._w_socks.remove(sock)
        except ValueError:
            pass

        self._r_socks.remove(sock)

        if sock in self._socks:
            self._socks[sock].handle_close()
            del self._socks[sock]
        else:
            self._sys.logger.debug("Closing listener socket FD: %d", sock.fileno())

        sock.shutdown(socket.SHUT_RDWR)

    def _request_write(self, sock):
        """Request passed socket as writable."""
        if sock not in self._w_socks:
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

            sock_lst = []
            sock_lst.append(self._serv_socks[sock].handle_init)  # current handler cb [0]
            sock_lst.append(0)  # expected number of bytes to receive next (buf) [1]
            sock_lst.append(None)  # recv cache [2]

            sock_lst[0](sock_lst[1])  # call stage_init(), passing state dict

            self._socks[acc_sock] = sock_lst
        else:
            # readable socket we are managing
            sock_state = self._socks[sock]

            try:
                chunk = sock.recv(sock_state[1])  # recv at most the current buf size
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
            elif len(chunk) < sock_state[1]:
                # num bytes recv is less than what is expected.
                sock_state[1] = sock_state[1] - len(chunk)  # bytes remaining
                sock_state[2] = sock_state[2] + chunk
            else:
                # received all expected bytes
                if sock_state[2] is not None:
                    chunk = sock_state[2] + chunk
                    sock_state[2] = None  # clear cache

                try:
                    ret_tup = sock_state[0](sock.fileno(), chunk)  # handle the chunk
                except TypeError:
                    self._sys.logger.error("Handler callback is not callable.")
                    raise

                if ret_tup is None:
                    # close the socket
                    self._close_socket(sock)
                else:
                    sock_state[0] = ret_tup[0]  # callback
                    sock_state[1] = ret_tup[1]  # buf size

    def writable_socket(self, sock):
        """
        Given a socket in a writable state, do something with it.

        Send whatever data is returned from the socket's associated handle_write() callback, and
        then switch the socket from being writable to readable.
        """
        s_data = self._socks[sock].handle_write()  # returns data to be written

        if s_data is not None:
            sock.send(s_data)

        self._w_socks.remove(sock)

    def add_listener(self, port, handler_cls):
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

        # initialize the handler and assign
        self._serv_socks[serv_sock] = handler_cls(_inject={
            '_sys': self._sys,
            'logger': self._sys.logger,
            'request_write': self._request_write
        })

        def connect_node(self, node_name):
            """Establish a connection using the passed node name."""
            try:
                cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cli_sock.setblocking(0)
            except socket.error as ex:
                self._sys.logger.error("Could not instantiate new client socket: %s", ex)
                raise

            conn_addr = self._sys.net.get_addr_from_name(node_name)
            cli_sock.connect_ex((conn_addr, self._port))  # use the default eMews daemon port

            self._r_socks.append(serv_sock)  # wait until we receive an ack from the receiving node
