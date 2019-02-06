'''
Provides functionality in a separate thread for socket communication between ConnectionManager's
listener and a client.  If client sends a service to run, then this thread will terminate with the
appropriate service to spawn.

Created on Mar 27, 2018

@author: Brian Ricks
'''
import select
import socket

import emews.base.commandhandler
import emews.base.irunnable

class ClientSession(emews.base.irunnable.IRunnable):
    '''
    classdocs
    '''
    def __init__(self, config, sock, thread_dispatcher):
        '''
        Constructor
        '''
        super(ClientSession, self).__init__(config)

        # currently supported acks
        self._ACK_MSG = {
            'success': 'OK\n',
            'fail': "ERR\n"
        }

        try:
            self._buf_size = self.config.get('receive_buffer')
            self._command_delim = self.config.get('command_delimiter')
        except emews.base.exceptions.KeychainException as ex:
            self.logger.error(ex)
            raise

        self._sock = sock  # socket used to receive commands

        self.logger.debug("Buffer size: %d", self._buf_size)

        self._interrupted = False  # true if stop() invoked (used to make sure shutdown called once)

        # CommandHandler (handles command processing, service spawning, etc...)
        # No component config options needed.
        self._command_handler = emews.base.commandhandler.CommandHandler(self.config.get_new(None),
                                                                         thread_dispatcher)
        self._command_count = 0  # successful commands processed

    def start(self):
        '''
        @Override from IRunnable
        '''
        # send ready to client
        if not self.__send_ack(self._ACK_MSG['success']):
            # issue when sending
            self._sock.close()
            return

        self.__listen()

        if not self._interrupted:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except socket.error as ex:
                self.logger.warning("Could not call shutdown() on socket: %s", ex)

        self._sock.close()
        self.logger.info("%d commands processed. Connection to client closed.", self._command_count)

    def stop(self):
        '''
        @Override from IRunnable
        We call socket shutdown as that will close the session and unblock the select.
        '''
        self._interrupted = True
        self._sock.shutdown(socket.SHUT_RDWR)

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

        if self._interrupted:
            # called here to reflect the proper threadName in the log
            self.logger.debug("Stop request received.  Shutting down...")

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
                # most likely client closed connection
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
            # TODO: refactor this
            bytes_sent = self._sock.send(ack_msg)
            while bytes_sent < len(ack_msg):
                try:
                    select.select([], [self._sock], [])
                except select.error as ex:
                    if not self._interrupted:
                        self.logger.warning("Select error on socket during active client session "\
                        "(ACK to send: %s, - during send of chunked data).", ack_msg)
                    else:
                        self.logger.debug(ex)
                    return False

                bytes_sent = self._sock.send(ack_msg[bytes_sent:])

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

        # delegate to CommandHandler
        try:
            result_continue = self._command_handler.process(cmd_tuple)
        except emews.base.commandhandler.CommandException:
            # If the ACK fails to send, then it's time to shut down the listener.
            return self.__send_ack(self._ACK_MSG['fail'])

        # command successful
        self._command_count += 1
        # If the ACK could not be sent or the ClientHandler told us to shut down, then time to shut
        # down the listener.
        return self.__send_ack(self._ACK_MSG['success']) and result_continue
