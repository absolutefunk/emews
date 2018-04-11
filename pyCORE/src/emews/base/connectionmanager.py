'''
Listens for new client connections and spawns ClientSessions when appropriate.

Created on Mar 24, 2018

@author: Brian Ricks
'''
import signal
import select
import socket

from emews.base.clientsession import ClientSession
from emews.base.thread_dispatcher import ThreadDispatcher

class ConnectionManager(object):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        # register signals
        signal.signal(signal.SIGHUP, self.shutdown_signal_handler)
        signal.signal(signal.SIGINT, self.shutdown_signal_handler)

        self._config = config
        self._logger = self._config.logger

        try:
            self._host = self._config.get('general', 'host')
            self._port = int(self._config.get('general', 'port'))
        except KeyError as ex:
            self._logger.error("Key %s not found in config.  "\
            "Check emews conf file for missing key.", ex)
            raise
        except ValueError as ex:
            self._logger.error("%s.  Check emews conf file for invalid values.", ex)
            raise

        # parameter checks
        if self._host == '':
            self._logger.warning("Host is not specified.  "\
            "Listener may bind to any available interface.")
        if self._port < 1 or self._port > 65535:
            self._logger.error("Port is out of range (must be between 1 and 65535, "\
            "given: %d)", self._port)
            raise ValueError("Port is out of range (must be between 1 and 65535, "\
            "given: %d)" % self._port)
        if self._port < 1024:
            self._logger.warning("Port is less than 1024 (given: %d).  "\
            "Elevated permissions may be needed for binding.", self._port)

        # handles thread spawning/management
        self._thread_dispatcher = ThreadDispatcher(self._config)

    def shutdown_signal_handler(self, signum, frame):
        '''
        Signal handler for incoming signals (those which may imply we need to shutdown)
        '''
        self._logger.info("Received signum %d, beginning shutdown.", signum)

    def start(self):
        '''
        starts the Listener
        '''
        self.listen()

    def listen(self):
        '''
        Listens for new incoming client connections.
        '''
        self._logger.debug("Starting listener, given host: %s, port: %d", self._host, self._port)

        try:
            serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Using select to block may be a bit more efficient than using the socket to block
            serv_sock.setblocking(0)
        except socket.error as ex:
            self._logger.error("Could not instantiate socket. %s", ex)
            return
        try:
            serv_sock.bind((self._host, self._port))
        except socket.error as ex:
            serv_sock.close()
            self._logger.error("Could not bind socket to interface. %s", ex)
            return
        try:
            serv_sock.listen(5)
        except socket.error as ex:
            serv_sock.close()
            self._logger.error("Exception when setting up connection requests. %s", ex)
            return

        self._logger.info("Listening on interface %s, port %d", self._host, self._port)

        while True:
            # Listen for new connections, and spawn off a new thread for each
            # connection made (this is to ensure the listener isn't held up if
            # a command is slow to reach a current connection).
            try:
                select.select([serv_sock], [], [])
            except select.error as ex:
                # this most likely will occur when select is interrupted
                self._logger.info("Listener no longer accepting incoming connections.")
                self._logger.debug(ex)
                break

            try:
                sock, src_addr = serv_sock.accept()
            except socket.error as ex:
                self._logger.error("Exception when accepting incoming connection.")
                self._logger.debug(ex)
                break

            self._logger.info("Connection established from %s", src_addr)
            self._thread_dispatcher.dispatch_thread(
                ClientSession(self._config, self._thread_dispatcher, sock))

        serv_sock.shutdown(socket.SHUT_RDWR)
        serv_sock.close()
