'''
Handles thread management.  Acts as a dispatcher for threads (ManagedThread)

Created on Mar 30, 2018

@author: Brian Ricks
'''
import threading

import emews.base.basedispatcher
from emews.base.managedthread import ManagedThread

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
        self._thr_lock = threading.Lock()
        self._active_threads = set()

    @property
    def count(self):
        '''
        Returns a count of active threads.
        '''
        return len(self._active_threads)


    def dispatch_thread(self, thread_cls, *args):
        '''
        Creates and dispatches a new ManagedThread.  thread_cls is the class object that we want to
        instantiate, and the args are additional args to pass to the thread class constructor during
        construction.
        '''
        try:
            thread_instance = thread_cls(self.config, *args)
        except TypeError as ex:
            self.logger.error("Could not instantiate passed thread_cls: %s", ex)
            raise

         # ManagedThread subscribes to 'stop_thread'
        managed_thread = ManagedThread(thread_instance, self.subscribe)
        # We subscribe to 'thread_stopping'
        managed_thread.subscribe('thread_stopping', self.remove_thread)
        # we also need to store the thread reference itself, so shutting down all threads we can
        # join each thread
        self._active_threads.add(managed_thread)

    def remove_thread(self, managed_thread):
        '''
        Removes a ManagedThread to the active list
        Called from a thread which needs to be removed.
        '''
        try:
            self._logger.debug("(%s) Acquiring lock...", managed_thread.name)
            with self._thr_lock:
                self._logger.debug("(%s) Lock acquired", managed_thread.name)
                self._active_threads.remove(managed_thread)
        except ValueError:
            self._logger.warning("Thread not found in the active list.")

        self._logger.debug("Thread %s removed from active thread list.", managed_thread.name)

    def shutdown_all_threads(self):
        '''
        Shuts down all the running threads.
        Called from a dispatcher which signals that it's time to shutdown everything.
        '''
        self._logger.info("%d running thread(s) to shutdown.", self._thr_state.count)

        self.dispatch('stop_thread')  # tells all subscribers (ManagedThread) to shutdown

        for active_thread in self._thr_state.active_threads:
            # Wait for each service to shutdown.  We put this in a separate loop so each service
            # will get the shutdown request first, and can shutdown concurrently.
            active_thread.join()
