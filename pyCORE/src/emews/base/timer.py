"""
Timer class that can be dispatched by a ThreadDispatcher.

Created on May 17, 2019
@author: Brian Ricks
"""
import threading

import emews.base.baseobject


class Timer(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_dispatcher',
                 '_timer_name',
                 '_interrupt_event',
                 '_duration',
                 '_callback',
                 '_callback_args')

    def __init__(self, duration, callback, callback_args):
        """Constructor."""
        self.sys = None  # not needed

        super(Timer, self).__init__()

        self._dispatcher = None
        self._interrupt_event = threading.Event()
        self._duration = duration
        self._callback = callback
        self._callback_args = callback_args

    def __str__(self):
        """Return the client name."""
        return self._timer_name

    def start(self):
        """Start the client."""
        self.logger.debug("%s: starting timer (duration: %d seconds) ...",
                          self._timer_name, self._duration)

        self._interrupt_event.wait(self._duration)

        self.logger.debug("%s: timer finished, invoking callback ...", self._timer_name)
        self._callback(*self._callback_args)

    def register_dispatcher(self, dispatcher):
        """Register the exit function of the dispatcher handling this timer."""
        self._dispatcher = dispatcher
        self.logger.debug("%s: dispatcher '%s' registered.", self._timer_name, str(dispatcher))

    def interrupt(self):
        """@Override Interrupt the client."""
        self._interrupt_event.set()
        super(Timer, self).interrupt()
        self.logger.debug("%s: finishing (asked to stop).", self._timer_name)
