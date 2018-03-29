'''
Provides functionality in a separate thread for socket communication between ServiceManager's
listener and a client.  If client sends a service to run, then this thread will terminate with the
appropriate service to spawn.

Created on Mar 27, 2018

@author: Brian Ricks
'''
import select
import socket

from mews.core.services.basethread import BaseThread

class ListenerThread(BaseThread):
    '''
    classdocs
    '''

    def __init__(self, config, thr_name, sock):
        '''
        Constructor
        '''
        BaseThread.__init__(self, config, thr_name)

        # currently supported commands
        self._COMMAND_MAPPING = {
            'S': self.__do_makeservice,  # add a service
            'E': self.__do_exit,         # exit
        }

        # currently supported acks
        self._ACK_MSG = {
            'success': 'OK\n',
            'fail': "ERR\n"
        }

        self._buf_size = config.get_sys('LISTENER', 'LISTENER_RECV_BUFFER')
        self._command_delim = config.get_sys('LISTENER', 'COMMAND_DELIMITER')

        self._sock = sock  # socket used to receive commands
        self._sock.setblocking(0)

        self._logger.debug("Buffer size: %d", self._buf_size)

        self._exit = False  # true once all commands are processed

    def run_service(self):
        '''
        Processes commands from client.
        Currently only one command is supported, that to start a service.
        '''
        # outer loop: loops per command
        while True:
            # inner loop: loops per data chunk (part of command)
            data_line = []
            line = ""
            chunk_count = 0
            while True:
                try:
                    select.select([self._sock], [], [])
                except select.error as ex:
                    self._logger.debug(ex)
                    self._sock.close()
                    return

                try:
                    data = self._sock.recv(self._buf_size)
                except socket.error as ex:
                    self._logger.error("Exception when receiving incoming data.")
                    self._logger.debug(ex)
                    self._sock.close()
                    return

                if not data:
                    self._logger.warning("Client abruptly closed the session.")
                    self._sock.close()
                    return

                chunk_count += 1
                # check if a carriage return is present in data
                term_index = data.find('\n')
                if term_index == -1:
                    data_line.append(data)
                    continue

                # truncate anything past the carriage return (and the carriage return)
                data = data[:term_index]
                data_line.append(data)
                line = "".join(data_line).strip()

                self._logger.debug("Received %d chunk(s).", chunk_count)
                self._logger.debug("Received line: %s", line)
                break

            cmd_tuple = self.process_line(line)

            if cmd_tuple is None or not self.process_command(cmd_tuple):
                # bad command or arg sent
                if not self.__send_ack(self._ACK_MSG['fail']):
                    return
            else:
                # command successful
                if not self.__send_ack(self._ACK_MSG['success']):
                    return

            if self._exit:
                break

        self._sock.close()

    def __send_ack(self, ack_msg):
        try:
            select.select([], [self._sock], [])
        except select.error as ex:
            self._logger.debug(ex)
            self._sock.close()
            return False

        try:
            self._sock.sendall(ack_msg)
        except socket.error as ex:
            self._logger.warning("Connection failure during active client session "\
            "(ACK to send: %s).", ack_msg)
            self._logger.debug(ex)
            self._sock.close()
            return False
        return True

    def process_line(self, line):
        '''
        Processes a line received from the socket.
        Returns a tuple of ['cmd', 'value'] if valid, otherwise none
        '''
        cmd_tuple = line.split(self._command_delim)

        if len(cmd_tuple) > 2:
            self._logger.warning("Command tuple too long (max size: 2, given: %d).", len(cmd_tuple))
            return None

        if len(cmd_tuple) == 1:
            # if no argument given, append one (some commands don't need arguments)
            cmd_tuple.append("")

        self._logger.debug("Command: %s, Arg: %s", cmd_tuple[0], cmd_tuple[1])

        return cmd_tuple

    def process_command(self, cmd_tuple):
        '''
        processes an incoming cmd/arg tuple
        '''
        if not self._COMMAND_MAPPING.has_key(cmd_tuple[0]):
            self._logger.warning("Command %s not recognized.", cmd_tuple[0])
            return False

        return self._COMMAND_MAPPING[cmd_tuple[0]](cmd_tuple[1])

    def __do_makeservice(self, service_str):
        '''
        Attempts to create a Service from the service_str.
        '''
        return True

    def __do_exit(self, arg_str):
        '''
        Exit the listener.
        '''
        self._logger.debug("Exit command processed.")
        self._exit = True
        return True
