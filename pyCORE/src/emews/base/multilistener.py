'''
Multi-connection listener, in which each accepted connection is passed off to a handler method.

When requested to stop, we shutdown the socket, which unblocks select.

Created on Apr 22, 2018
@author: Brian Ricks
'''
import os
import select
import socket

import emews.base.baselistener

class MultiListener(emews.base.baselistener.BaseListener):
    '''
    classdocs
    '''
    def __init__(self, config, handler_listener):
        '''
        Constructor
        '''
        super(MultiListener, self).__init__(config)
        # callback class for providing listener handling
        self._handler_listener = handler_listener

        self._interrupted = False  # sets to true when stop() invoked

    @property
    def interrupted(self):
        '''
        returns whether the listener has been requested to stop
        '''
        return self._interrupted

    def listen(self):
        '''
        @Override starts the listening loop for connections
        '''
        while not self._interrupted:
            try:
                select.select([self.socket], [], [])
            except select.error as ex:
                # interrupted (most likely)
                if self.interrupted:
                    self.logger.info("Listener no longer accepting incoming connections.")
                    break
                else:
                    self.logger.error("Select error while blocking on listener socket.")
                    raise StandardError(ex)

            try:
                sock, src_addr = self.socket.accept()
            except socket.error as ex:
                # Just ignore this exception, as emews can keep running
                self.logger.warning("Exception when accepting incoming connection: %s", ex)
                continue

            self.logger.info("Connection established from %s", src_addr)
            sock.setblocking(0)
            self._handler_listener.handle_accepted_connection(sock)   # call connection handler

    def stop(self):
        '''
        @Override Invoked when it is time to shut down.
        '''
        self._interrupted = True
        self.socket.shutdown()
