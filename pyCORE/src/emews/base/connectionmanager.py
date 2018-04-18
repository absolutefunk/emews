'''
Listens for new client connections and spawns ClientSessions when appropriate.

Created on Mar 24, 2018

@author: Brian Ricks
'''
import select
import signal
import socket

import emews.base.baseobject
from emews.base.clientsession import ClientSession
from emews.base.thread_dispatcher import ThreadDispatcher

class ConnectionManager(emews.base.baseobject.BaseObject):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(ConnectionManager, self).__init__(config)

        # register signals
        signal.signal(signal.SIGHUP, self.shutdown_signal_handler)
        signal.signal(signal.SIGINT, self.shutdown_signal_handler)

        try:
            self._host = self.config.get_sys('general', 'host')
            self._port = self.config.get_sys('general', 'port')
        except ValueError as ex:
            self.logger.error("In emews config: %s", ex)
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

        # handles thread spawning/management
        self._thread_dispatcher = ThreadDispatcher(self.config)

    def shutdown_signal_handler(self, signum, frame):
        '''
        Signal handler for incoming signals (those which may imply we need to shutdown)
        '''
        self.logger.info("Received signum %d, beginning shutdown...", signum)

        # Select is unblocked when this returns.

    def start(self):
        '''
        starts the Listener
        '''
        self.listen()

        # We want the listener to be shut down before executing the thread shutdown, hence why we
        # call it here instead of in shutdown_signal_handler().
        self._thread_dispatcher.shutdown_all_threads()

    def listen(self):
        '''
        Listens for new incoming client connections.
        '''
        self.logger.debug("Starting listener, given host: %s, port: %d", self._host, self._port)

        try:
            serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Using select to block may be a bit more efficient than using the socket to block
            serv_sock.setblocking(0)
        except socket.error as ex:
            self.logger.error("Could not instantiate socket. %s", ex)
            return
        try:
            serv_sock.bind((self._host, self._port))
        except socket.error as ex:
            serv_sock.close()
            self.logger.error("Could not bind socket to interface. %s", ex)
            return
        try:
            serv_sock.listen(5)
        except socket.error as ex:
            serv_sock.close()
            self.logger.error("Exception when setting up connection requests. %s", ex)
            return

        self.logger.info("Listening on interface %s, port %d", self._host, self._port)

        while True:
            # Listen for new connections, and spawn off a new thread for each
            # connection made (this is to ensure the listener isn't held up if
            # a command is slow to reach a current connection).
            try:
                select.select([serv_sock], [], [])
            except select.error as ex:
                # this most likely will occur when select is interrupted
                self.logger.info("Listener no longer accepting incoming connections.")
                self.logger.debug(ex)
                break

            try:
                sock, src_addr = serv_sock.accept()
            except socket.error as ex:
                self.logger.error("Exception when accepting incoming connection.")
                self.logger.debug(ex)
                break

            self.logger.info("Connection established from %s", src_addr)
            self._thread_dispatcher.dispatch_thread(
                ClientSession(self.config, self._thread_dispatcher, sock))

        serv_sock.shutdown(socket.SHUT_RDWR)
        serv_sock.close()
