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

    def __init__(self, wrapped_object, autostart=True):
        '''
        Constructor
        '''
        self._thread_name = self.__class__.__name__ + "-%d" % ThreadWrapper.__current_thread_id
        self._wrapped_object = wrapped_object

        # Target is outside the class.  We pass this instance to it.
        self._thread = threading.Thread(name=self._thread_name, target=self.run_thread)

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
        starts the thread
        '''
        self._wrapped_object.context_name(self._thread_name)
        self._thread.start()

    def run_thread(self):
        '''
        Invokes the start() method on the wrapped_object (in a separate thread).
        '''
        self._wrapped_object.start()

    def stop(self):
        '''
        Should enable graceful shutdown of this thread.
        '''
        self._wrapped_object.stop()
