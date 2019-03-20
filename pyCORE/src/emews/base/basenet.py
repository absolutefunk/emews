"""
Base class for backend daemon networking.

Sockets in this framework are intialized to be non-blocking, enabling graceful shutdown from the
daemon process.

Created on Feb 21, 2019
@author: Brian Ricks
"""
import select


"""
NOTE:  Refactor this to be integrated into eMews node-to-node communication.  Do not use this as a
general framework for services, as service devs can just use raw sockets, no sense doing all this
extra work.  for services, self.sys.net.* functions for network helper functions (stuff like
resolving IP address by node name).

Use netserver.py within ConnectionManager.  Delete other net classes that are no longer needed.
"""


class BaseNet(object):
    """Classdocs."""

    __slots__ = ('_sys', '_interrupted', '_r_socks', '_w_socks')

    def __init__(self, sysprop):
        """Constructor."""
        super(BaseNet, self).__init__()
        self._sys = sysprop
        self._interrupted = False

        # TODO: use sets here (maybe wrap a set in a class compatible with list method calls)
        self._r_socks = []  # list of socket objects to manage for a readable state
        self._w_socks = []  # list of socket objects to manage for a writable state

    def start(self):
        """Start the main net loop."""
        while not self._interrupted:
            try:
                r_sock_list, w_sock_list, _ = select.select(self._r_socks, self._w_socks, [])
            except select.error:
                if not self._interrupted:
                    self._sys.logger.error("Select error while blocking on managed sockets.")
                    raise
                self._sys.logger.debug("Select interrupted.")

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

    def interrupt(self):
        """Set the interrupt flag."""
        self._interrupted = True

        # TODO: have a way to unblock the select()
