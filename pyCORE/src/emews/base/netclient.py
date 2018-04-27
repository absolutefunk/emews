'''
TCP client implementation.  Basically a wrapper for basic socket tasks.

Created on Apr 26, 2018
@author: Brian Ricks
'''
import select
import socket

import emews.base.baseobject
import emews.base.inet

class NetClient(emews.base.baseobject.BaseObject, emews.base.inet.INet):
    '''
    classdocs
    '''
    def __init__(self, config, handler_client):
        '''
        Constructor
        '''
        super(NetClient, self).__init__(config)

        self._handler_client = handler_client

        self._interrupted = False  # sets to true when stop() invoked

        # inputs (fds)
        self._inputs = [self.socket]
        self._outputs = []

        # required params
        try:
            self._host = self.config.get('host')
            self._port = self.config.get('port')
            self._recv_timeout = self.config.get('recv_timeout')
        except emews.base.exceptions.KeychainException as ex:
            self.logger.error(ex)
            raise

        # parameter checks
        if self._host == '':
            self.logger.error("Host is not specified (required).")
            raise ValueError("Host is not specified (required).")
        if self._port < 1 or self._port > 65535:
            self.logger.error("Port is out of range (must be between 1 and 65535, "\
            "given: %d)", self._port)
            raise ValueError("Port is out of range (must be between 1 and 65535, "\
            "given: %d)" % self._port)

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setblocking(0)
        except socket.error as ex:
            self.logger.error("Could not instantiate socket. %s", ex)
            raise

    @property
    def socket(self):
        '''
        @Override Returns a socket (client socket if client, listener socket if listener).
        '''
        return self._socket

    @property
    def interrupted(self):
        '''
        @Override returns whether the net-based object has been requested to stop
        '''
        return self._interrupted

    def request_write(self, sock):
        '''
        @Override This is called when a socket is requested to be written to.
        '''
        if sock is not self.socket:
            self.logger.error("passed socket is not our socket.")
            raise StandardError("passed socket is not our socket.")

        self._inputs.remove(sock)
        self._outputs.append(sock)


    def start(self):
        '''
        Starts the net-based logic.
        '''
        self._socket.connect((self._host, self._port))
        self._run()

    def _run(self):
        '''
        Main logic for client.
        '''
        while not self.interrupted:
            try:
                r_socks, w_socks, e_socks = select.select(self._inputs, self._outputs, self._inputs)
            except select.error as ex:
                # interrupted (most likely)
                if self.interrupted:
                    self.logger.info("Net client shutting down ...")
                    break
                else:
                    self.logger.error("Select error while blocking on client socket.")
                    raise StandardError(ex)

            for r_sock in r_socks:
                # there should only be one sock
                if r_sock is not self.socket:
                    self.logger.error("Unknown socket in select readable list.")
                    raise StandardError("Unknown socket in select readable list.")
                self._handler_listener.handle_readable_socket(r_sock)

            for w_sock in w_socks:
                # there should only be one sock
                if w_sock is not self.socket:
                    self.logger.error("Unknown socket in select writable list.")
                    raise StandardError("Unknown socket in select writable list.")
                self._outputs.remove(w_sock)
                self._inputs.append(w_sock)
                self._handler_listener.handle_writable_socket(w_sock)

    def stop(self):
        '''
        @Override Invoked when it is time to shut down.
        '''
        self._interrupted = True
        self.socket.shutdown(socket.SHUT_RDWR)
