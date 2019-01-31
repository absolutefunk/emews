"""
Wraps an object to provide threading support.

Created on Mar 26, 2018
@author: Brian Ricks
"""
import threading

import emews.base.irunnable


class ThreadWrapper(emews.base.irunnable.IRunnable):
    """Classdocs."""

    __slots__ = ('_thread_name', '_wrapped_object', '_thread')
    __current_thread_id = 0  # each thread has a unique id assigned (for logging)

    def __init__(self, wrapped_object, autostart=True, daemon=True):
        """Constructor."""
        self._thread_name = wrapped_object.__class__.__name__ + "-%d" % \
            ThreadWrapper.__current_thread_id
        ThreadWrapper.__current_thread_id += 1

        self._wrapped_object = wrapped_object
        self._thread = threading.Thread(name=self._thread_name, target=self._wrapped_object.start())

        self._thread.setDaemon(daemon)

        if autostart:
            self.start()

    @property
    def name(self):
        """Return a given name for the thread."""
        return self._thread_name

    def start(self):
        """@Override start the thread."""
        self._thread.start()

    def stop(self):
        """@Override graceful shutdown of this thread."""
        self._wrapped_object.stop()

    def join(self, timeout=None):
        """Invoke the join method of threading.Thread."""
        self._thread.join(timeout)
