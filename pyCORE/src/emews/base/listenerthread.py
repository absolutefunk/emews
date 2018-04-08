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
import emews.base.clienthandler

class ListenerThread(BaseThread):
    '''
    classdocs
    '''
    def __init__(self, sys_config, thr_name, sock, cb_exit):
        '''
        Constructor
        '''
        super(ListenerThread, self).__init__(self, sys_config, thr_name)

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

        self._interrupted = False  # true if stop() invoked (used to make sure shutdown called once)

        # ClientHandler (handles command processing, service spawning, etc...)
        self._client_handler = emews.base.clienthandler.ClientHandler(self.config)
        self._command_count = 0  # successful commands processed

    def stop(self):
        '''
        @Override of BaseThread stop().
        We call socket shutdown as that will close the session and unblock the select.
        '''
        self.logger.info("Stop request received.  Shutting down.")
        self._interrupted = True
        self._sock.shutdown(socket.SHUT_RDWR)

    def run_thread(self):
        '''
        @Override from BaseThread
        '''
        self.__listen()

        if not self._interrupted:
            self._sock.shutdown(socket.SHUT_RDWR)

        self._sock.close()
        self.logger.info("%d commands processed.", self._command_count)

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
        # loops per command
        while not self._interrupted:
            line = self.get_line()

            if not line or not self.process_line(line):
                # something happened or we were told to exit, time to exit
                break

        return

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
                if not self._interrupted:
                    self.logger.warning("Select error on socket during active client session "\
                    "(trying to receive data).")
                else:
                    self.logger.debug(ex)
                return ""

            try:
                data = self._sock.recv(self._buf_size)
            except socket.error as ex:
                if not self._interrupted:
                    self.logger.warning("Socket error when receiving incoming data.")
                else:
                    self.logger.debug(ex)
                return ""

            if not data:
                if not self._interrupted:
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
            if not self._interrupted:
                self.logger.warning("Select error on socket during active client session "\
                "(ACK to send: %s).", ack_msg)
            else:
                self.logger.debug(ex)
            return False

        try:
            self._sock.sendall(ack_msg)
        except socket.error as ex:
            if not self._interrupted:
                self.logger.warning("Socket error during active client session "\
                "(ACK to send: %s).", ack_msg)
            else:
                self.logger.debug(ex)
            return False

        return True

    def process_line(self, line):
        '''
        Processes a line received from the socket.  Returns False if it's time to shut down the
        listener, True to continue listening for commands.
        '''
        cmd_tuple = line.split(self._command_delim)

        if len(cmd_tuple) == 1:
            # if no argument given, append one (some commands don't need arguments)
            cmd_tuple.append("")

        # delegate to ClientHandler
        try:
            result_continue = self._client_handler.process(cmd_tuple)
        except emews.base.clienthandler.ClientCommandException as ex:
            # bad command or arg, or some other issue occurred with command processing
            self.logger.debug(ex)
            # If the ACK fails to send, then it's time to shut down the listener.
            return self.__send_ack(self._ACK_MSG['fail'])

        # command successful
        self._command_count += 1
        # If the ACK could not be sent or the ClientHandler told us to shut down, then time to shut
        # down the listener.
        return self.__send_ack(self._ACK_MSG['success']) and result_continue
