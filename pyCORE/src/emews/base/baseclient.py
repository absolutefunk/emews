"""
Base class for networking clients.

Created on Apr 18, 2019
@author: Brian Ricks
"""
from abc import abstractmethod
import threading

import emews.base.baseobject


class BaseClient(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_dispatcher', '_client_name', '_interrupt_event', '_conn_timeout',
                 '_conn_max_attempts')

    def __init__(self):
        """Constructor."""
        super(BaseClient, self).__init__()

        self._dispatcher = None
        self._interrupt_event = threading.Event()

    def __str__(self):
        """Return the client name."""
        return self._client_name

    def start(self):
        """Start the client."""
        self.logger.debug("%s: starting client ...", self._client_name)
        self.run_client()

    @abstractmethod
    def run_client(self):
        """Where the service entrance code goes.  Must be implemented by child class."""
        pass

    def register_dispatcher(self, dispatcher):
        """Register the exit function of the dispatcher handling this net client."""
        self._dispatcher = dispatcher
        self.logger.debug("%s: dispatcher '%s' registered.", self._client_name, str(dispatcher))

    def sleep(self, time):
        """Block the client for the given amount of time (in seconds)."""
        if self._interrupted or time <= 0:
            return

        self._interrupt_event.wait(time)

    def interrupt(self):
        """@Override Interrupt the client."""
        self._interrupt_event.set()
        super(BaseClient, self).interrupt()
        self.logger.debug("%s: finishing (asked to stop).", self._client_name)
