'''
Spawns new service threads and handles their management.

Created on Mar 24, 2018

@author: Brian Ricks
'''

import logging
import socket
from threading import Thread

from mews.core.services.servicecontrol import ServiceControl

class ServiceSpawner(object):
    '''
    classdocs
    '''

    def __init__(self, config):
        '''
        Constructor
        '''
        self._logger = logging.getLogger(config.logbase)
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
    def listener(self):
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
            sock, src_addr = serv_sock.accept()  # TODO: may need to be in separate thread (management)
            self._logger.info("Connection from %s", src_addr)
