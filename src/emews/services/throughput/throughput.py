"""
Throughput stats.

Currently outputs to the eMews log send/recv throughput for all interfaces on the node this service
is running on.

Created on Aug 9, 2018
@author: Brian Ricks
"""
import socket

import psutil

import emews.services.baseservice


class Throughput(emews.services.baseservice.BaseService):
    """Classdocs."""

    __slots__ = ('_if_info')

    def __init__(self, config):
        """Constructor."""
        super(Throughput, self).__init__()

        interface_prefixes = config['interface_prefixes']  # list

        self._if_info = None  # stores current interface info
        self._init_ifs(interface_prefixes)

    def _init_ifs(self, interface_prefixes):
        """Initialize interface dict with the interfaces we want to monitor."""
        self._if_info = dict()

        ifs = psutil.net_if_addrs()
        for if_name, if_addrs in ifs.items():
            for prefix in interface_prefixes:
                if not if_name.startswith(prefix):
                    continue

                # interface is in our prefix list
                self._if_info[if_name] = {}
                # create addr string
                ipv4_str = "0.0.0.0"
                # ipv6_str = "::0"
                for if_addr in if_addrs:
                    if if_addr.family == socket.AF_INET:
                        ipv4_str = if_addr.address
                    # elif if_addr.family == socket.AF_INET6:
                    #    ipv6_str = if_addr.address

                self._if_info[if_name]['addr_str'] = ipv4_str
                # create other map keys
                self._if_info[if_name]['b_sent'] = 0  # number of sent bytes (total)
                self._if_info[if_name]['b_recv'] = 0  # number of received bytes (total)

    def run_service(self):
        """@Override Output throughput on all interfaces once a second (roughly)."""
        while not self.interrupted:
            msg_str = ""
            net_stats = psutil.net_io_counters(pernic=True)

            for if_name, if_info in self._if_info.iteritems():
                msg_str += if_info.get('addr_str') + ": "
                bytes_sent = net_stats.get(if_name).bytes_sent
                bytes_recv = net_stats.get(if_name).bytes_recv

                # throughput in kbps
                tr_sent = ((bytes_sent - if_info.get('b_sent')) * 8) / 1024.0
                tr_recv = ((bytes_recv - if_info.get('b_recv')) * 8) / 1024.0
                msg_str += "[S: %.2f kbps, R: %.2f kbps] " % (tr_sent, tr_recv)
                # update the total bytes sent/recv
                if_info['b_sent'] = bytes_sent
                if_info['b_recv'] = bytes_recv

            self.logger.info(msg_str)

            # Poll once a second.  Note that this is not entirely accurate, as this just delays
            # a second after the logic above has completed.  Thus, throughput as displayed here
            # may be slightly higher than the actual throughput (given that delay is exactly a
            # second).
            self.sleep(1.0)
