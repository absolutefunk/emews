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

        # inputs (fds)
        self._inputs = [self.socket]

    def stop(self):
        '''
        @Override Invoked when it is time to shut down.
        '''
        self._interrupted = True
        self.socket.shutdown(socket.SHUT_RDWR)  # will unblock select()

        self._shutdown()

    def _shutdown(self):
        '''
        shuts down sockets
        '''
        for sock in self._inputs:
            # self.socket is closed in BaseListener
            if sock is not self.socket:
                sock.close()

    def request_close(self, sock):
        '''
        This is called when a socket needs to be closed.
        Note, this is veryr important for this type of listener.  Be sure to recognize when a
        readable socket needs to be closed (when socket.recv() returns no data).  Not checking
        for this and simply returning could result in an infinite loop as the socket will never
        block on read.
        '''
        if not sock in self._inputs:
            self.logger.warning("Given socket not in inputs list.  Ignoring ...")
            return

        self._inputs.remove(sock)
        sock.close()

        self.logger.debug("Closed and removed accepted socket.")

    def listen(self):
        '''
        @Override starts the listening loop for connections
        '''
        while not self.interrupted:
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
                        acc_sock, src_addr = r_sock.accept()
                        acc_sock.setblocking(0)
                    except socket.error as ex:
                        # ignore the exception, but dump the new connection
                        self.logger.warning("Socket exception while accepting connection: %s", ex)
                        continue  # continue the for loop for r_socks

                    self.logger.info("Connection established from %s", src_addr)
                    self._inputs.append(acc_sock)
                    self._handler_listener.handle_accepted_connection(acc_sock)
                else:
                    # some socket we are managing (not the listener socket)
                    self._handler_listener.handle_readable_socket(r_sock)

            for e_sock in e_socks:
                # well, this sucks...
                self.logger.warning("Socket in exceptional state.  Removing ...")
                self._inputs.remove(e_sock)
