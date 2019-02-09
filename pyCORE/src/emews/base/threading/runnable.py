"""
Runnable class base.

Created on Feb 8, 2019
@author: Brian Ricks
"""

from threading import Event


class Runnable(object):
    """Classdocs."""

    __slots__ = ('_interrupted', '_interrupt_event')

    def __init__(self):
        """Constructor."""
        self._interrupt_event = Event()  # used to interrupt Event.wait() on stop()
        self._interrupted = False  # set to true on stop()

    @property
    def interrupted(self):
        """Interrupted state of the runnable."""
        return self._interrupted

    def interrupt(self):
        """Interrupt the runnable."""
        self._service_interrupt_event.set()
        self._interrupted = True

    def sleep(self, time):
        """Block the runnable for the given amount of time (in seconds)."""
        if self._interrupted:
            return

        self._service_interrupt_event.wait(time)
