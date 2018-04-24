'''
Multi-connection asynchronous listener, in which each accepted connection is managed by
MultiASyncListener.  Interaction with each connection is accomplished through callbacks.

When requested to stop, we shutdown the sockets, which unblocks select.

Created on Apr 23, 2018
@author: Brian Ricks
'''
import select
import socket

import emews.base.baselistener

class MultiASyncListener(emews.base.baselistener.BaseListener):
    '''
    classdocs
    '''
    def __init__(self, config, handler_listener):
        '''
        Constructor
        '''
        super(MultiASyncListener, self).__init__(config)
        # callback class for providing listener handling
        self._handler_listener = handler_listener

        self._interrupted = False

        # inputs (fds)
        self._inputs = [self.socket]

    @property
    def interrupted(self):
        '''
        returns whether the listener has been requested to stop
        '''
        return self._interrupted

    def stop(self):
        '''
        @Override Invoked when it is time to shut down.
        '''
        self._interrupted = True
        self.socket.shutdown()  # will unblock select()

    def listen(self):
        '''
        @Override starts the listening loop for connections
        '''
        while not self._interrupted:
            try:
                r_socks, _, e_socks = select.select(self._inputs, [], self._inputs)
            except select.error as ex:
                # interrupted (most likely)
                if self.interrupted:
                    self.logger.info("NetServ no longer accepting incoming connections.")
                    break
                else:
                    self.logger.error("Select error while blocking on managed sockets.")
                    raise StandardError(ex)

            for r_sock in r_socks:
                if r_sock is self.socket:
                    # this is the listener socket
                    try:
                        sock = r_sock.accept()
                    except socket.error as ex:
                        # ignore the exception, but dump the new connection
                        self.logger.warning("Socket exception while accepting connection: %s", ex)
                        continue  # continue the for loop for r_socks

                    self._inputs.append(r_sock)
                    self._handler_listener.handle_accepted_connection(sock)
                else:
                    # some socket we are managing (not the listener socket)
                    self._handler_listener.handle_readable_socket(sock)

            for e_sock in e_socks:
                # well, this sucks...
                self.logger.warning("Socket in exceptional state.  Removing ...")
                self._inputs.remove(e_sock)
