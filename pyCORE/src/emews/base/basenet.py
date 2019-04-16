"""
Base class for backend daemon networking.

Sockets in this framework are intialized to be non-blocking, enabling graceful shutdown from the
daemon process.

Created on Feb 21, 2019
@author: Brian Ricks
"""
import select

import emews.base.logger


"""
TODO:  Refactor this to be integrated into eMews node-to-node communication.  Do not use this as a
general framework for services, as service devs can just use raw sockets, no sense doing all this
extra work.  for services, self.sys.net.* functions for network helper functions (stuff like
resolving IP address by node name).

Use netserver.py within ConnectionManager.  Delete other net classes that are no longer needed.
"""


class NetProto(object):
    """Enumerations for supported protocols."""

    __slots__ = ()

    ENUM_SIZE = 6

    NET_NONE = 0       # placeholder
    NET_CC_1 = 1       # CC channel (future)
    NET_CC_2 = 2       # CC channel (future)
    NET_LOGGING = 3    # distributed logging
    NET_AGENT = 4      # agent-based communication
    NET_HUB = 5        # hub-based communication


class HandlerCB(object):
    """Enumerations for ConnectionManager handler methods."""

    __slots__ = ()

    ENUM_SIZE = 2

    REQUEST_CLOSE = 0
    REQUEST_WRITE = 1

    # state constants
    STATE_ACK_OK = 17
    STATE_ACK_NOK = 18


class BaseNet(object):
    """Classdocs."""

    __slots__ = ('logger', '_interrupted', '_r_socks', '_w_socks', '_e_socks')

    def __init__(self):
        """Constructor."""
        self.logger = emews.base.logger.get_logger()
        self._interrupted = False

        # TODO: use sets here (maybe wrap a set in a class compatible with list method calls)
        self._r_socks = []  # list of socket objects to manage for a readable state
        self._w_socks = []  # list of socket objects to manage for a writable state
        self._e_socks = []  # list of socket objects to manage for an exceptional state

    def start(self):
        """Start the main net loop."""
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
                self.handle_writable_socket(w_sock)

            for r_sock in r_sock_list:
                # readable sockets
                self.handle_readable_socket(r_sock)

            for e_sock in e_sock_list:
                # exceptional sockets
                self.handle_exceptional_socket(e_sock)

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
