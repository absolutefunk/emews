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

    __slots__ = ('_host', '_port', '_socks', '_listener_sock', '_net_serv', '_pending_ids',
                 '_cb', '_hub_addr', '_conn_timeout', '_conn_max_attempts')

    def __init__(self, config_comm, config_hub, sysprop):
        """Constructor."""
        super(ConnectionManager, self).__init__(sysprop)

        self._hub_addr = config_hub['node_address']

        self._conn_timeout = config_comm['connect_timeout']
        self._conn_max_attempts = config_comm['connect_max_attempts']

        self._port = config_comm['port']
        self._host = config_comm['host']
        if self._host is None:
            self._host = ''  # any available interface

        self._socks = {}  # accepted sockets
        self._pending_ids = {}  # FDs (socks) that are pending an established connection
        self._listener_sock = None  # listener socket (will be instantiated on start())

        self._net_serv = emews.base.netserv.NetServ(self.sys)

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

        super(ConnectionManager, self).start()

    def stop(self):
        """Stop the ConnectionManager."""
        self.interrupt()

        # shutdown the listener socket first
        self._close_socket(self._listener_sock)

        for sock in self._socks.keys():
            # shut down all managed sockets
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
            self._e_socks.append(acc_sock)

            # call handle_init(), sock FD as session_id, IPv4 address as int
            self._net_serv.handle_init(
                acc_sock.fileno(), struct.unpack(">I", socket.inet_aton(src_addr[0]))[0])

            sock_state = []
            sock_state.append(self._net_serv.handle_connection)  # current handler cb [0]
            sock_state.append(6)  # expected number of bytes to receive next (buf) [1]
            sock_state.append("")  # recv/send data cache [2]

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

    def hub_query(self, request, param=0):
        """
        Given a request, return the corresponding result.

        Note that this is a client-side (blocking) operation, and thus is expected to run either
        under the main thread before ConnectionManager starts, or from a service thread.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self._conn_timeout)
        connect_attempts = 0

        while not self._interrupted and connect_attempts < self._conn_max_attempts:
            try:
                sock.connect((self._hub_addr, self._port))

                if self._interrupted:
                    break

                sock.sendall(struct.pack('>HLHL',
                                         emews.base.basenet.NetProto.NET_HUB,
                                         self.sys.node_id,
                                         request,  # request to the hub node
                                         param  # param (0=None)
                                         ))

                if self._interrupted:
                    break

                # If a signal is caught to shutdown, but the socket does not catch it (say because
                # it is running from another thread than the main one), the hub node will catch it
                # and close the socket from its side, unblocking it here.
                chunk = sock.recv(4)  # query result (4 bytes)

                if self._interrupted:
                    break

                result = struct.unpack('>L', chunk)
            except (socket.error, struct.error):
                connect_attempts += 1
                continue

            break

        try:
            sock.shutdown()
        except socket.error:
            pass

        sock.close()

        if self._interrupted:
            raise KeyboardInterrupt()

        if connect_attempts == self._conn_max_attempts:
            # query failed
            self.logger.warning("Exhausted attempts to fulfill query.")
            raise IOError("Exhausted attempts to fulfill query.")

        return result
