'''
Spawns new service threads and handles their management.

Created on Mar 24, 2018

@author: Brian Ricks
'''

import logging
import signal
import socket

from mews.core.services.servicethread import ServiceThread
from mews.core.listenerthread import ListenerThread

class ServiceManager(object):
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

        self._logbase = config.logbase
        self._logger = logging.getLogger(config.logbase)
        self._threadID = 0  # increments each time a thread is spawned
        self._listener_config = {}
        self._listener_config['listener_recv_buffer'] = config['LISTENER_RECV_BUFFER']

        try:
            self._host = config.get('host')
            self._port = int(config.get('port'))
        except KeyError as ex:
            self._logger.error("Key %s not found in config.  "\
            "Check pyCORE conf file for missing key.", ex)
            raise
        except ValueError as ex:
            self._logger.error("%s.  Check pyCORE conf file for invalid values.", ex)
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

        self._services = []  # list of all services (ServiceThread) currently running

    def __get_next_thread_id(self):
        self._threadID += 1
        return self._threadID

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
        Listens for new incoming services to spawn
        '''
        self._logger.debug("Starting listener, given host: %s, port: %d", self._host, self._port)

        try:
            serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
            serv_sock.listen(1)
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
                sock, src_addr = serv_sock.accept()
            except socket.error as ex:
                # this most likely will occur when the socket is interrupted
                self._logger.info("Listener no longer accepting incoming connections.")
                self._logger.debug(ex)
                serv_sock.close()
                break

            self._logger.info("Connection established from %s", src_addr)
            listener_thread = ListenerThread(self._logbase, "ListenerThread-%d" %
                                             self.__get_next_thread_id(),
                                             sock, self._max_listener_retries)
            listener_thread.start()

        self.shutdown()

    def shutdown(self):
        '''
        Shuts down all the running services.
        '''
        self._logger.info("%d running services to shutdown.", len(self._services))

        for service_thread in self._services:
            service_thread.stop()
        for service_thread in self._services:
            # Wait for each service to shutdown.  We put this in a separate loop so each service
            # will get the shutdown request first, and can shutdown concurrently.
            service_thread.join()
