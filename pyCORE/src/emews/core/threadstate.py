'''
Handles thread state information.

Created on Mar 30, 2018

@author: Brian Ricks
'''
import threading

def thread_names_str():
    '''
    Concatenates active thread names to a space delim string.
    '''
    thread_names = []
    for thread in threading.enumerate():
        thread_names.append(thread.name)

    return ", ".join(thread_names)

class ThreadState(object):
    '''
    Keeps state of all running threads (spawned from this one).
    '''
    class ActiveThreadIter(object):
        '''
        Iterator for the active_thread list.
        '''
        def __init__(self, active_threads):
            '''
            Constructor
            '''
            self._current_index = 0
            self._active_threads = active_threads

        def __iter__(self):
            return self

        def next(self):
            '''
            Returns the next active thread object.
            '''
            if self._current_index < len(self._active_threads):
                self._current_index += 1
                return self._active_threads[self._current_index - 1]
            else:
                raise StopIteration()

    def __init__(self, sys_config):
        '''
        Constructor
        '''
        self._logger = sys_config.logger
        self._thr_lock = threading.Lock()
        self._active_threads = []

    @property
    def count(self):
        '''
        Returns a count of active threads.
        '''
        return len(self._active_threads)

    @property
    def active_threads(self):
        '''
        Returns an iterator over active threads.
        '''
        return ThreadState.ActiveThreadIter(self._active_threads)

    def add_thread(self, base_thread):
        '''
        adds a BaseThread to the active list
        '''
        self._active_threads.append(base_thread)
        self._logger.debug("Thread %s added to active thread list.", base_thread.name)
        self._logger.info("%d threads currently active.", threading.active_count())
        self._logger.debug("Active threads: [%s].", thread_names_str())

    def remove_thread(self, base_thread):
        '''
        removes a BaseThread to the active list
        '''
        try:
            self._logger.debug("(%s) Acquiring lock...", base_thread.name)
            with self._thr_lock:
                self._logger.debug("(%s) Lock acquired", base_thread.name)
                self._active_threads.remove(base_thread)
        except ValueError:
            self._logger.warning("Thread not found in the active list.")

        self._logger.debug("Thread %s removed from active thread list.", base_thread.name)
