"""
Network client functionality.

Created on Apr 17, 2019
@author: Brian Ricks
"""
import socket
import struct

import emews.base.baseclient
import emews.base.baseobject


# client classes - these run in separate threads and are suitable for ThreadDispatcher dispatch
class BroadcastMessage(emews.base.baseclient.BaseClient):
    """Broadcasts a message across the network."""

    __slots__ = ('_port', '_message', '_interval', '_duration', '_sock')

    def __init__(self, port, message, interval, duration):
        """Constructor."""
        super(BroadcastMessage, self).__init__()

        self._port = port
        self._message = message
        self._interval = interval
        self._duration = duration
        self._sock = None

    def start(self):
        """Start the broadcast."""
        self.logger.debug("%s: Broadcast starting ...", self._client_name)
        self.broadcast()

    def broadcast(self):
        """Run the broadcast."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        elapsed_time = 0

        # not the most precise way of time keeping, but good enough
        while elapsed_time < self._duration and not self._interrupted:
            self.sleep(self._interval)
            elapsed_time += self._interval
            try:
                self._sock.sendto(self._message, ('255.255.255.255', self._port))
            except socket.error:
                continue

        self._sock.close()
        self._sock = None
        self.logger.debug("%s: Broadcast finished.", self._client_name)

    def stop(self):
        """Stop the broadcast."""
        self.interrupt()
        self.logger.debug("%s: Broadcast finishing (asked to stop).", self._client_name)


class NetClient(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_port', '_hub_addr', '_conn_timeout', '_conn_max_attempts', '_num_clients')

    def __init__(self, config, hub_addr):
        """Constructor."""
        super(NetClient, self).__init__()

        self._port = config['port']
        self._hub_addr = hub_addr

        self._conn_timeout = config['connect_timeout']
        self._conn_max_attempts = config['connect_max_attempts']

        self._num_clients = 0

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

    def _get_client_instance(self, class_def, *args):
        """Return an inject dict for new net clients."""
        inject_dict = {}
        inject_dict['sys'] = self.sys
        inject_dict['_client_name'] = class_def.__name__ + str(self._num_clients)
        inject_dict['_conn_timeout'] = self._conn_timeout
        inject_dict['_conn_max_attempts'] = self._conn_max_attempts

        self._num_clients += 1

        return class_def(*args, _inject=inject_dict)

    # clients which need to run in a thread - these methods return an object suitable for dispatch
    def broadcast_message(self, message, interval, duration):
        """Broadcast a message using the given interval, over the given duration."""
        return self._get_client_instance(BroadcastMessage, self._port, message, interval, duration)
