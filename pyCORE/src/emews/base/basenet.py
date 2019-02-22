"""
Base class for node-to-node networking.

Sockets in this framework are intialized to be non-blocking, enabling graceful shutdown from the
daemon process.

Created on Apr 22, 2018
@author: Brian Ricks
"""
import select


"""
# once the listener is finished, then close the socket
self._socket.close()

NOTE:  Refactor this to be integrated into eMews node-to-node communication.  Do not use this as a
general framework for services, as service devs can just use raw sockets, no sense doing all this
extra work.  for services, self.sys.net.* functions for sending data to other nodes and stuff:
-- something like self.sys.net.send_to_node(node_id)
--- This isn't needed if the service has the socket already
-- maybe also: self.net.send_to_all_services(data)
---- Looks like I'm going to need a receive() method for BaseService, I dunno, think about all this.
"""


class BaseNet(object):
    """Classdocs."""

    __slots__ = ('_r_socks', '_w_socks')

    def __init__(self, sysprop):
        """Constructor."""
        super(BaseNet, self).__init__()

        # TODO: does select.select accept sets?
        self._r_socks = []  # list of socket objects to manage for a readable state
        self._w_socks = []  # list of socket objects to manage for a writable state

    def start(self):
        """Start the main net loop."""
        while not self.interrupted:
            try:
                r_sock_list, w_sock_list, _ = select.select(self._r_socks, self._w_socks, [])
            except select.error:
                if not self.interrupted:
                    self.logger.error("Select error while blocking on managed sockets.")
                    raise

            for r_sock in r_sock_list:
                # readable sockets
                self.handle_readable_socket(r_sock)

            for w_sock in w_sock_list:
                # writable sockets
                self.handle_writable_socket(w_sock)

    def readable_socket(self, sock):
        """
        Given a socket in a readable state, do something with it.

        This method should be overridden by any subclass which handles readable sockets.
        """
        pass

    def writable_socket(self, sock):
        """
        Given a socket in a writable state, do something with it.

        This method should be overridden by any subclass which handles writable sockets.
        """
        pass
