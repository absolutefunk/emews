"""
Network client functionality.

Created on Apr 17, 2019
@author: Brian Ricks
"""
import socket
import struct

import emews.base.baseobject


class NetClient(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_port', '_hub_addr', '_conn_timeout', '_conn_max_attempts')

    def __init__(self, config, hub_addr):
        """Constructor."""
        super(NetClient, self).__init__()

        self._port = config['port']
        self._hub_addr = hub_addr
        self._conn_timeout = config['connect_timeout']
        self._conn_max_attempts = config['connect_max_attempts']

    def hub_query(self, request, param=0):
        """
        Given a request, return the corresponding result.

        Note that this is a client-side (blocking) operation, and thus is expected to run either
        under the main thread before ConnectionManager starts, or from a service thread.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self._conn_timeout)
        connect_attempts = 0

        while not self._interrupted and connect_attempts < self._conn_max_attempts:
            try:
                sock.connect((self._hub_addr, self._port))

                if self._interrupted:
                    break

                sock.sendall(struct.pack('>HLHL',
                                         emews.base.basenet.NetProto.NET_HUB,
                                         self.sys.node_id,
                                         request,  # request to the hub node
                                         param  # param (0=None)
                                         ))

                if self._interrupted:
                    break

                # If a signal is caught to shutdown, but the socket does not catch it (say because
                # it is running from another thread than the main one), the hub node will catch it
                # and close the socket from its side, unblocking it here.
                chunk = sock.recv(4)  # query result (4 bytes)

                if self._interrupted:
                    break

                result = struct.unpack('>L', chunk)
            except (socket.error, struct.error):
                connect_attempts += 1
                continue

            break

        try:
            sock.shutdown()
        except socket.error:
            pass

        sock.close()

        if self._interrupted:
            raise KeyboardInterrupt()

        if connect_attempts == self._conn_max_attempts:
            # query failed
            self.logger.warning("Exhausted attempts to fulfill query.")
            raise IOError("Exhausted attempts to fulfill query.")

        return result
