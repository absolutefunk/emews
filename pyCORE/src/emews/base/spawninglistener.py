'''
Spawning listener, in which each accepted connection is spawned to its own thread.  The class to
spawn is passed in to the constructor.  To pass custom arguments to the constructor once a
connection is accepted, a callback method must be implemented in the child class which returns a
list of arguments which will be passed to the spawned class.

When requested to stop, a pipe is written to which unblocks select.select.  This way the listener
does not have to be run in the main thread, and we don't have to resort to polling.

Created on Apr 22, 2018
@author: Brian Ricks
'''
from abc import abstractmethod
import os
import select
import socket

import emews.base.baselistener
import emews.base.thread_dispatcher

class SpawningListener(emews.base.baselistener.BaseListener):
    '''
    classdocs
    '''
    def __init__(self, config, spawn_cls):
        '''
        Constructor
        '''
        super(SpawningListener, self).__init__(config)

        self._spawn_class = spawn_cls
        self._interrupted = False  # sets to true when stop() invoked

        # handles thread spawning/management
        self._thread_dispatcher = emews.base.thread_dispatcher.ThreadDispatcher(self.config)

        # We need to setup a pipe that we can write to for unblocking select.select when stop()
        # is invoked.  This is necessary as only the main thread will receive signals.
        _, self._int_write_fd = os.pipe()

    @abstractmethod
    def update_spawnclass_args(self):
        '''
        Provides a way to pass arguments to the constructor of the spawn class.  Return as a list
        the args that the spawn class requires.  Note that the first arg is the config, and second
        arg the sock (don't return these).  If nothing to return, just return None.
        '''
        pass

    @property
    def interrupted(self):
        '''
        returns whether the listener has been requested to stop
        '''
        return self._interrupted

    @property
    def dispatcher(self):
        '''
        Returns the ThreadDispatcher.  Useful if dispatching object requires passing the dispatcher
        in its constructor.
        '''
        return self._thread_dispatcher

    def listen(self):
        '''
        @Override starts the listening loop for multi-threading support
        '''
        while not self._interrupted:
            # Listen for new connections, and spawn off a new thread for each
            # connection made.  Note, self._int_write_pipe will only be written to if we need to
            # shutdown.
            try:
                select.select([self.socket], [self._int_write_pipe], [])
            except select.error as ex:
                # this most likely will occur when select is interrupted
                self.logger.info("Listener no longer accepting incoming connections.")
                self.logger.debug(ex)
                break

            try:
                sock, src_addr = self.socket.accept()
            except socket.error as ex:
                self.logger.error("Exception when accepting incoming connection.")
                self.logger.debug(ex)
                break

            self.logger.info("Connection established from %s", src_addr)
            obj_args = self.update_spawnclass_args()  # returned value must be a list (or None)
            self._thread_dispatcher.dispatch_thread(self._spawn_class(self.config, sock, *obj_args))

        os.close(self._int_write_fd)  # close the pipe

        self._thread_dispatcher.shutdown_all_threads()  # start threads shutdown

    def stop(self):
        '''
        @Override Invoked when it is time to shut down.
        '''
        self._interrupted = True
        # We want the listener to be shut down before executing the thread shutdown
        # 'signal' to select to unblock (if blocked)
        os.write(self._int_write_fd, "B")
