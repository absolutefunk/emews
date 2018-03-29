'''
Spawns new service threads and handles their management.

Created on Mar 24, 2018

@author: Brian Ricks
'''

import logging
import signal
import select
import socket
import threading

from mews.core.listenerthread import ListenerThread

def thread_names_str():
    '''
    Concatenates active thread names to a space delim string.
    '''
    thread_names = []
    for thread in threading.enumerate():
        thread_names.append(thread.name)

    return ", ".join(thread_names)

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

        self._thr_lock = threading.Lock()

        self._config = config
        self._logger = logging.getLogger(self._config.logbase)

        try:
            self._host = self._config.get('host')
            self._port = int(self._config.get('port'))
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

        self._active_threads = []  # list of all threads (BaseThread) currently running

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
            listener_thread = ListenerThread(self._config, "ListenerThread", sock,
                                             self.remove_thread)
            listener_thread.start()

            self.add_thread(listener_thread)

        serv_sock.shutdown(socket.SHUT_RDWR)
        serv_sock.close()
        self.shutdown()

    def add_thread(self, base_thread):
        '''
        adds a BaseThread to the active list
        '''
        self._active_threads.append(base_thread)
        self._logger.info("%d threads currently active.", threading.active_count())
        self._logger.debug("Active threads: [%s].", thread_names_str())

    def remove_thread(self, base_thread):
        '''
        removes a BaseThread to the active list
        '''
        try:
            self._logger.debug("(%s) Acquiring lock...", base_thread.name)
            with self._thr_lock:
                self._logger.debug("(%s) Lock acquired", base_thread.name)
                self._active_threads.remove(base_thread)
        except ValueError:
            self._logger.warning("Thread not found in the active list.")

        self._logger.debug("Thread %s removed from active thread list.", base_thread.name)

    def shutdown(self):
        '''
        Shuts down all the running threads.
        '''
        self._logger.info("%d running threads to shutdown.", len(self._active_threads))

        for active_thread in self._active_threads:
            self._logger.debug("Stopping thread %s.", active_thread.name)
            active_thread.stop()
        for active_thread in self._active_threads:
            # Wait for each service to shutdown.  We put this in a separate loop so each service
            # will get the shutdown request first, and can shutdown concurrently.
            active_thread.join()
