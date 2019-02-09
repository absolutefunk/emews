"""
Wraps an object to provide threading support.

Created on Mar 26, 2018
@author: Brian Ricks
"""
import threading

import emews.components.importer
import emews.components.samplers.zerosampler


class ThreadSpawn(object):
    """Classdocs."""

    __slots__ = ('_thread_name', '_wrapped_object', '_thread', '_thread_loop')
    __current_thread_id = 0  # each thread has a unique id assigned (for logging)

    def __init__(self, sysprop, config, wrapped_object):
        """Constructor."""
        self._thread_name = wrapped_object.__class__.__name__ + "-%d" % \
            ThreadSpawn.__current_thread_id

        ThreadSpawn.__current_thread_id += 1

        self._wrapped_object = wrapped_object
        self._thread = threading.Thread(name=self._thread_name, target=self._wrapped_object.start())
        if 'loop' in config and config['loop']:
            if 'loop_using_sampler' in config:
                self._thread_loop = emews.components.importer.instantiate(
                    config['loop']['loop_using_sampler'])
            else:
                self._thread_loop = emews.components.samplers.zerosampler.ZeroSampler()
        else:
            self._thread_loop = None

        self._thread.setDaemon(config['daemon'])

        if config['autostart']:
            self.start()

    @property
    def name(self):
        """Return a given name for the thread."""
        return self._thread_name

    @property
    def interrupted(self):
        """Interrupted state of the wrapped_object."""
        return self._wrapped_object.interrupted

    def start(self):
        """Start the thread."""
        if not self._wrapped_object.interrupted:
            if self._thread_loop is not None:
                self._start_loop()
            else:
                self._thread.start()

    def _start_loop(self):
        """Start the thread."""
        if not self._wrapped_object.interrupted:
            self._thread.start()
            self._wrapped_object.sleep(self._thread_loop.sample())

    def stop(self):
        """Graceful shutdown of this thread."""
        self._wrapped_object.stop()

    def join(self, timeout=None):
        """Invoke the join method of threading.Thread."""
        self._thread.join(timeout)
