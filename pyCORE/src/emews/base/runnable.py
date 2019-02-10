"""
Runnable class base.

Created on Feb 8, 2019
@author: Brian Ricks
"""

import threading


class Runnable(object):
    """Classdocs."""

    __slots__ = ('_interrupted', '_interrupt_event')

    def __init__(self):
        """Constructor."""
        self._interrupt_event = threading.Event()  # used to interrupt Event.wait() on stop()
        self._interrupted = False  # set to true on stop()

    @property
    def interrupted(self):
        """Interrupted state of the runnable."""
        return self._interrupted

    def interrupt(self):
        """Interrupt the runnable."""
        self._interrupt_event.set()
        self._interrupted = True

    def sleep(self, time):
        """Block the runnable for the given amount of time (in seconds)."""
        if self._interrupted or time <= 0:
            return

        self._interrupt_event.wait(time)
