'''
Provides functionality in a separate thread for socket communication between ServiceManager's
listener and a client.  If client sends a service to run, then this thread will terminate with the
appropriate service to spawn.

Created on Mar 27, 2018

@author: Brian Ricks
'''
import logging
import socket

from mews.core.services.basethread import BaseThread

class ListenerThread(BaseThread):
    '''
    classdocs
    '''

    def __init__(self, logbase, name, sock, config):
        '''
        Constructor
        '''
        BaseThread.__init__(self, logbase, name)

        # currently supported commands
        self._COMMAND_MAPPING = {
            'S': self.__do_makeservice,  # add a service
            'E': self.__do_exit,         # exit
        }

        self._logger = logging.getLogger(logbase)
        self._sock = sock  # socket used to receive commands
        self._buf_size = config['listener_recv_buffer']

        self._logger.debug("max retries: %d, buffer size: %d", self._retries, self._buf_size)

        self._exit = False  # true once all commands are processed

    def run_service(self):
        '''
        Processes commands from client.
        Currently only one command is supported, that to start a service.
        '''
        data_line = []
        line = ""
        # outer loop: loops per command
        while True:
            # inner loop: loops per data chunk (part of command)
            while True:
                data = self._sock.recv(self._buf_size)
                # check if a carriage return is present in data
                term_index = data.find('\n')
                if term_index == -1:
                    data_line.append(data)
                    continue

                # truncate anything past the carriage return (and the carriage return)
                data = data[term_index - 1]
                data_line.append(data)
                line = "".join(data_line).strip()
                data_line = []
                break

            cmd_tuple = self.process_line(line)

            if cmd_tuple is None or not self.process_command(cmd_tuple):
                # bad command or arg sent
                try:
                    self._sock.sendall("ERR")
                except socket.error as ex:
                    self._logger.warning("Connection termination during active client session.")
                    self._logger.debug(ex)
                    self._sock.close()
                    return

            if self._exit:
                break

    def process_line(self, line):
        '''
        Processes a line received from the socket.
        Returns a tuple of ['cmd', 'value'] if valid, otherwise none
        '''
        cmd_tuple = line.split(": ")

        if len(cmd_tuple) != 2:
            return None

        self._logger.debug("Command: %s, Arg: %s", cmd_tuple[0], cmd_tuple[1])

        if len(cmd_tuple[0]) != 1:
            return None

        return cmd_tuple

    def process_command(self, cmd_tuple):
        '''
        processes and incoming cmd/arg tuple
        '''
        if not self._COMMAND_MAPPING.has_key(cmd_tuple[0]):
            return False

        return self._COMMAND_MAPPING[cmd_tuple[0]](cmd_tuple[1])

    def __do_makeservice(self, service_str):
        '''
        Attempts to create a Service from the service_str.
        '''
        return True

    def __do_exit(self):
        '''
        Exit the listener.
        '''
        self._logger.debug("Exit command processed, shutting down socket and exiting.")
        self._sock.close()
        self._exit = True
        return True
