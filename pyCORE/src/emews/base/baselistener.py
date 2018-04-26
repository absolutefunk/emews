'''
Base class for socket-based network listeners.  A listener is analogous to python's ServerSocket,
but is written to incorporate unblocking on signals, as fast unblocking is important for quick
emulator shutdown.  Hence, the listener socket is set to be non-blocking.

Created on Apr 22, 2018
@author: Brian Ricks
'''
from abc import abstractmethod
import socket

import emews.base.baseobject
import emews.base.exceptions
import emews.base.inet

class BaseListener(emews.base.baseobject.BaseObject, emews.base.inet.INet):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(BaseListener, self).__init__(config)

        self._interrupted = False  # sets to true when stop() invoked

        try:
            self._host = self.config.get('host')
            self._port = self.config.get('port')
        except emews.base.exceptions.KeychainException as ex:
            self.logger.error(ex)
            raise

        # parameter checks
        if self._host == '':
            self.logger.warning("Host is not specified.  "\
            "Listener may bind to any available interface.")
        if self._port < 1 or self._port > 65535:
            self.logger.error("Port is out of range (must be between 1 and 65535, "\
            "given: %d)", self._port)
            raise ValueError("Port is out of range (must be between 1 and 65535, "\
            "given: %d)" % self._port)
        if self._port < 1024:
            self.logger.warning("Port is less than 1024 (given: %d).  "\
            "Elevated permissions may be needed for binding.", self._port)

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setblocking(0)
        except socket.error as ex:
            self.logger.error("Could not instantiate socket. %s", ex)
            raise

    @property
    def socket(self):
        '''
        @Override returns the listener socket
        '''
        return self._socket

    @property
    def interrupted(self):
        '''
        @Override returns whether the net-based object has been requested to stop
        '''
        return self._interrupted

    def start(self):
        '''
        @Override starts the listener
        '''
        try:
            self._socket.bind((self._host, self._port))
        except socket.error as ex:
            self._socket.close()
            self.logger.error("Could not bind socket to interface. %s", ex)
            raise
        try:
            self._socket.listen(5)
        except socket.error as ex:
            self._socket.close()
            self.logger.error("Exception when setting up connection requests. %s", ex)
            raise

        self.logger.info("Listening on interface %s, port %d", self._host, self._port)
        self.listen()

        # once the listener is finished, then close the socket
        self._socket.close()

    @abstractmethod
    def listen(self):
        '''
        Invokes the listening procedure.
        '''
        pass

    def stop(self):
        '''
        @Override Requests the listener to stop.
        '''
        pass
