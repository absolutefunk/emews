'''
Provides a centralized point for distributed log collection over a network.

Only one node will have a LogServer.  The system.yml config will specify the node.  The other nodes
will be able to look up the logserver node, and forward log entries to it.

When using distributed logging, the formatting configuration in system.yml would be applied to
LogServer if LogServer is the final destination for the log entries.  If LogServer is acting as a
collection and forward server, then no formatting is applied.

Created on Apr 22, 2018
@author: Brian Ricks
'''
import os
import pickle
import select
import socket
import struct

import emews.base.baseobject
import emews.base.irunnable
import emews.base.spawninglistener

class LogServer(emews.base.spawninglistener.SpawningListener):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(LogServer, self).__init__(config, LogHandler)

    def update_spawnclass_args(self):
        '''
        @Override
        '''

class LogHandler(emews.base.baseobject.BaseObject, emews.base.irunnable.IRunnable):
    '''
    Handles log entries from a single source.
    '''
    def __init__(self, config, sock):
        '''
        Constructor
        '''
        super(LogHandler, self).__init__(config)

        self._socket = sock
        self._interrupted = False  # true if stop() invoked (used to make sure shutdown called once)
        _, self._int_write_fd = os.pipe()  # write to unblock select.select()

    def stop(self):
        '''
        @Override Called to signal that the implementing class needs to gracefully exit all tasks.
        '''
        self._interrupted = True
        os.write(self._int_write_fd, "B")

    def start(self):
        '''
        @Override Called to start execution of implementing task.
        '''
        while not self._interrupted:
            try:
                select.select([self._socket], [self._int_write_fd], [])
                chunk = self._socket.recv(4)
                if len(chunk) < 4:
                    break

                slen = struct.unpack('>L', chunk)[0]
                select.select([self._socket], [self._int_write_fd], [])
                chunk = self._socket.recv(slen)
                while len(chunk) < slen:
                    select.select([self._socket], [self._int_write_fd], [])
                    chunk = chunk + self._socket.recv(slen - len(chunk))
            except socket.error as ex:
                if not self._interrupted:
                    self.logger.warning("Socket error when receiving incoming data.")
                else:
                    self.logger.debug(ex)
                return
            except select.error as ex:
                if not self._interrupted:
                    self.logger.warning("Select error on socket (trying to receive data).")
                else:
                    self.logger.debug(ex)
                return

            obj = pickle.loads(chunk)

        os.close(self._int_write_fd)  # close the pipe
