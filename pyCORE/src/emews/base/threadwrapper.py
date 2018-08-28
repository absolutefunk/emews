'''
Wraps an object to provide threading support.

Created on Mar 26, 2018
@author: Brian Ricks
'''
import threading

import emews.base.irunnable

class ThreadWrapper(emews.base.irunnable.IRunnable):
    '''
    classdocs
    '''
    __current_thread_id = 0  # each thread has a unique id assigned (for logging)

    def __init__(self, wrapped_object, autostart=True, daemon=True):
        '''
        Constructor
        '''
        self._thread_name = wrapped_object.__class__.__name__ + "-%d" % \
            ThreadWrapper.__current_thread_id
        ThreadWrapper.__current_thread_id += 1

        self._wrapped_object = wrapped_object
        self._thread = threading.Thread(name=self._thread_name, target=self.run_thread)

        self._thread.setDaemon(daemon)

        if autostart:
            self.start()

    @property
    def name(self):
        '''
        returns a given name for the thread
        '''
        return self._thread_name

    def start(self):
        '''
        @Override starts the thread
        '''
        self._thread.start()

    def run_thread(self):
        '''
        Invokes the start() method on the wrapped_object (in a separate thread).
        '''
        try:
            self._wrapped_object.start()
        except Exception as ex:  # pylint: disable=W0703
            self.logger.error("[%s] Raised exception: %s",
                              self._wrapped_object.__class__.__name__, ex)

    def stop(self):
        '''
        @Override Should enable graceful shutdown of this thread.
        '''
        self._wrapped_object.stop()

    def join(self, timeout=None):
        '''
        Invokes the join method of threading.Thread.
        '''
        self._thread.join(timeout)
