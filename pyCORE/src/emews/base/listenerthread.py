'''
Provides functionality in a separate thread for socket communication between ServiceManager's
listener and a client.  If client sends a service to run, then this thread will terminate with the
appropriate service to spawn.

Created on Mar 27, 2018

@author: Brian Ricks
'''
import select
import socket

from emews.base.basethread import BaseThread

class ListenerThread(BaseThread):
    '''
    classdocs
    '''
    def __init__(self, sys_config, thr_name, sock, cb_exit):
        '''
        Constructor
        '''
        super(ListenerThread, self).__init__(self, sys_config, thr_name)

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

        self._buf_size = self.config.get_sys('listener', 'receive_buffer')
        self._command_delim = self.config.get_sys('listener', 'command_delimiter')

        # TODO: In standalone mode, REMOVE_THREAD_CALLBACK is not needed.  Perhaps a key in
        # sys_config to let service know if it was spawned through ServiceManager or standalone?
        self._callback_exit = cb_exit

        self._sock = sock  # socket used to receive commands
        self._sock.setblocking(0)

        self.logger.debug("Buffer size: %d", self._buf_size)

        self._exit = False  # true once all commands are processed or stop() invoked
        self._interrupted = False  # true if stop() invoked (used to make sure shutdown called once)

    def stop(self):
        '''
        @Override of BaseThread stop().
        We call socket shutdown as that will close the session and unblock the select.
        '''
        self.logger.info("Stop request received.  Shutting down.")
        self._exit = True
        self._interrupted = True
        self._sock.shutdown(socket.SHUT_RDWR)

    def run_thread(self):
        '''
        @Override from BaseThread
        '''
        command_count = self.__listen()

        if not self._interrupted:
            self._sock.shutdown(socket.SHUT_RDWR)

        self._sock.close()
        self.logger.info("%d commands processed.", command_count)

        if not self._interrupted:
            # Remove self from active thread list in ServiceManager.
            # Note, if shutting down due to interrupt, then most likely triggered by the
            # ServiceManager, so we don't want to delete the reference from its list as the
            # ServiceManager is still using the list.
            self._callback_exit(self)

    def __listen(self):
        '''
        Processes commands from client.
        Currently only one command is supported, that to start a service.
        '''
        command_count = 0  # successful commands processed
        # loops per command
        while not self._exit:
            line = self.get_line()

            if not line:
                # something happened, time to exit
                break

            if self.process_line(line):
                # command successfully processed
                command_count += 1

        return command_count

    def get_line(self):
        '''
        Gets a line of data, \n terminated.
        '''
        data_line = []
        line = ""
        chunk_count = 0
        while True:
            # loops per data chunk (part of command)
            try:
                select.select([self._sock], [], [])
            except select.error as ex:
                self.logger.debug(ex)
                return ""

            try:
                data = self._sock.recv(self._buf_size)
            except socket.error as ex:
                self.logger.error("Exception when receiving incoming data.")
                self.logger.debug(ex)
                return ""

            if not data:
                if not self._exit:
                    # If self._exit is True here, it means stop() was invoked, and we closed
                    # the session.
                    self.logger.warning("Session abruptly closed.")
                else:
                    self.logger.debug("Session closed.")

                return ""

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

            self.logger.debug("Received %d chunk(s).", chunk_count)
            self.logger.debug("Received line: %s", line)
            break

        return line

    def __send_ack(self, ack_msg):
        try:
            select.select([], [self._sock], [])
        except select.error as ex:
            self.logger.debug(ex)
            return False

        try:
            self._sock.sendall(ack_msg)
        except socket.error as ex:
            self.logger.warning("Connection failure during active client session "\
            "(ACK to send: %s).", ack_msg)
            self.logger.debug(ex)
            return False
        return True

    def process_line(self, line):
        '''
        processes a line received from the socket
        '''
        cmd_tuple = line.split(self._command_delim)

        if len(cmd_tuple) == 1:
            # if no argument given, append one (some commands don't need arguments)
            cmd_tuple.append("")

        if not self.process_command(cmd_tuple):
            # bad command or arg sent
            if not self.__send_ack(self._ACK_MSG['fail']):
                self._exit = True

            return False

        # command successful
        if not self.__send_ack(self._ACK_MSG['success']):
            # the command still counts, but the ACK may not have been received by the client
            self._exit = True

        return True

    def process_command(self, cmd_tuple):
        '''
        processes the command that the line represents
        '''
        #TODO: generalize (commands) to services with cmdline args
        self.logger.debug("Command: %s, Arg: %s", cmd_tuple[0], cmd_tuple[1])

        if not cmd_tuple[0] in self._COMMAND_MAPPING:
            self.logger.warning("Command %s not recognized.", cmd_tuple[0])
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
        self.logger.debug("Exit command processed.")
        self._exit = True
        return True
