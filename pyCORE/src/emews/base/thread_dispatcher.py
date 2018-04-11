'''
Handles thread management.  Acts as a dispatcher for threads.

Created on Mar 30, 2018

@author: Brian Ricks
'''
import threading
from weakref import WeakSet

import emews.base.basedispatcher
from emews.base.threadwrapper import ThreadWrapper

def thread_names_str():
    '''
    Concatenates active thread names to a space delim string.
    '''
    thread_names = []
    for thread in threading.enumerate():
        thread_names.append(thread.name)

    return ", ".join(thread_names)

class ThreadDispatcher(emews.base.basedispatcher.BaseDispatcher):
    '''
    Dispatches and manages active threads (ManagedThread).
    The following events are used:
    stop_thread: called when subscribing threads need to shut down
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(ThreadDispatcher, self).__init__(config)
        # When a thread dies, it is automatically removed from the _active_threads set.
        self._active_threads = WeakSet()

    @property
    def count(self):
        '''
        Returns a count of active threads.
        '''
        return len(self._active_threads)


    def dispatch_thread(self, object_instance):
        '''
        Creates and dispatches a new ThreadWrapper.  object_instance is the object that we want to
        wrap around ThreadWrapper.
        '''
        wrapped_object = ThreadWrapper(object_instance)

        # subscribe wrapped_object to our 'stop_thread' event
        self.subscribe('stop_thread', wrapped_object.stop)
        # we also need to store the thread reference itself, so shutting down all threads we can
        # join each thread
        self._active_threads.add(wrapped_object)

    def shutdown_all_threads(self):
        '''
        Shuts down all the running threads.
        Called from a dispatcher which signals that it's time to shutdown everything.
        '''
        self._logger.info("%d running thread(s) to shutdown.", self._thr_state.count)

        self.dispatch('stop_thread')  # tells all subscribers to shutdown

        for active_thread in self._thr_state.active_threads:
            # Wait for each service to shutdown.  We put this in a separate loop so each service
            # will get the shutdown request first, and can shutdown concurrently.
            active_thread.join()
