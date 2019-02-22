"""
Listens for new client connections and spawns ClientSessions when appropriate.

Created on Mar 24, 2018
@author: Brian Ricks
"""
import emews.base.clientsession
import emews.base.netserver


class ConnectionManager(object):
    """Classdocs."""

    __slots__ = ('_netserver', '_thread_dispatcher')

    def __init__(self, config, sysprop, thread_dispatcher):
        """Constructor."""
        super(ConnectionManager, self).__init__()

        self._netserver = emews.base.netserver.NetServer(config, sysprop, self)
        self._thread_dispatcher = thread_dispatcher

    def stop(self):
        """Stop the ConnectionManager."""
        self._netserver.interrupt()
