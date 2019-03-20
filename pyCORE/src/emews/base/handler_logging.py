"""
Provides a centralized point for distributed log collection over a network.

Created on Apr 22, 2018
@author: Brian Ricks
"""
import logging
import pickle
import struct

from emews.base.connectionmanager import HandlerCB


class HandlerLogging(object):
    """Classdocs."""

    __slots__ = ('_sys')

    def __init__(self, sysprop):
        """Constructor."""
        self._sys = sysprop

    def handle_init(self, state_dict):
        """Initialize state dict."""
        state_dict['stage'] = 0
        state_dict['msg'] = ""

    def handle_read(self, chunk, state_dict):
        """Handle a chunk of data."""
        read_stage = state_dict['stage']

        if read_stage == 0:
            # log message length (4 bytes)
            state_dict['msg'] = state_dict['msg'] + chunk
            if len(state_dict['msg']) == 4:
                try:
                    slen = struct.unpack('>L', state_dict['msg'])[0]
                except struct.error as ex:
                    self._sys.logger.warning("Struct error when unpacking log message length: %s",
                                             ex)
                    return HandlerCB.REQUEST_CLOSE
                state_dict['stage'] = 1
                state_dict['slen'] = slen
                state_dict['msg'] = ""
            elif len(state_dict['msg']) > 4:
                # what we received is not a valid struct
                self._sys.logger.warning("Log message length struct larger than expected length.")
                return HandlerCB.REQUEST_CLOSE

        elif read_stage == 1:
            # partial or whole log message
            state_dict['msg'] = state_dict['msg'] + chunk

            if len(state_dict['msg']) == state_dict['slen']:
                # received the entire message
                self.process_message(self._sock_state['msg'])  # handle the msg
                return HandlerCB.REQUEST_CLOSE
            elif len(state_dict['msg']) > state_dict['slen']:
                # too much data received, synchronization between stages may be off
                self._sys.logger.warning("Log message larger than expected length.")
                return HandlerCB.REQUEST_CLOSE

        return HandlerCB.NO_REQUEST

    def process_message(self, msg):
        """Process the complete log message."""
        log_record = logging.makeLogRecord(pickle.loads(msg))
        self._sys.logger.handle(log_record)
