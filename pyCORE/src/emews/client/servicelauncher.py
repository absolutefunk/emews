"""
Client for requesting services to spawn in eMews.  Sends a single request per invocation.

Created on Apr 26, 2018
@author: Brian Ricks
"""
import argparse
import os
import random
import signal
import socket
import struct
import threading

import emews.base.config
import emews.base.enums


class SingleServiceClient(object):
    """Classdocs."""

    __slots__ = ('_port', '_service_name', '_service_config_path', '_connect_timeout',
                 '_connect_max_attempts', '_interrupted')

    def __init__(self, config, service_name, service_config_path):
        """Constructor."""
        self._port = config['communication']['port']
        self._connect_timeout = config['communication']['connect_timeout']
        self._connect_max_attempts = config['communication']['connect_max_attempts']

        self._service_name = service_name
        self._service_config_path = service_config_path

        self.interrupted = False

    def start(self):
        """Connect to eMews daemon and send command."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self._connect_timeout)
        connect_attempts = 0
        ack = None

        while connect_attempts < self._connect_max_attempts and not self.interrupted:
            try:
                sock.connect(('127.0.0.1', self._port))

                if self.interrupted:
                    break

                sock.sendall(struct.pack('>HLHL',
                                         emews.base.enums.net_protocols.NET_SPAWN,
                                         0,  # node id (clients don't have a node id, leave at zero)
                                         emews.base.enums.spawner_protocols.SPAWNER_LAUNCH_SERVICE,
                                         len(self._service_name),  # params (service name length)
                                         len(self._service_config_path)  # config length
                                         ))

                if self.interrupted:
                    break

                sock.sendall(self._service_name)

                if self.interrupted:
                    break

                sock.sendall(struct.pack('L',
                                         len(self._service_config_path)  # config length
                                         ))

                if self.interrupted:
                    break

                sock.sendall(self._service_config_path)

                if self.interrupted:
                    break

                chunk = sock.recv(4)  # ACK (2 bytes)

                if self.interrupted:
                    break

                ack = struct.unpack('>H', chunk)
            except (socket.error, struct.error):
                connect_attempts += 1
                continue
            except KeyboardInterrupt:
                try:
                    # this may fail if socket endpoint is already closed
                    sock.shutdown(socket.SHUT_RDWR)
                except socket.error:
                    pass

                sock.close()
                raise

            break

        try:
            # this most likely will fail as the hub node should have closed the connection
            sock.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass

        sock.close()

        if connect_attempts == max_attempts:
            raise IOError("Could not send service launch command to eMews daemon.")
        elif ack == emews.base.enums.net_state.STATE_NACK:
            raise IOError("Received NACK from eMews daemon.")


def main():
    """Do setup and launch."""
    parser = argparse.ArgumentParser(description='eMews Service Launcher')
    parser.add_argument("-s", "--sys_config", help="path of the eMews system config file "
                        "(default: emews root)")
    parser.add_argument("-c", "--node_config", help="path of the eMews node-based config file "
                        "(default: <none>)")
    parser.add_argument("-c", "--service_config", help="path of the service config file"
                        "(default: standard path and name)")
    parser.add_argument("service", help="name of the service class to load")
    args = parser.parse_args()

    client = None
    client_wait = threading.Event()

    def shutdown_signal_handler(signum, frame):
        """Handle when a registered signal is caught (ctrl-c for example)."""
        client_wait.set()
        client.interrupted = True

    signal.signal(signal.SIGHUP, shutdown_signal_handler)
    signal.signal(signal.SIGINT, shutdown_signal_handler)

    # config
    base_config = emews.base.config.parse(os.path.join(root_path, 'base/conf.yml'))
    if args.sys_config is None:
        system_config = emews.base.config.parse(os.path.join(root_path, 'system.yml'))
    else:
        system_config = emews.base.config.parse(os.path.join(root_path, args.sys_config))
    node_config = emews.base.config.parse(args.node_config) \
        if args.node_config is not None else {}
    config_dict_system = emews.base.config.merge_configs(
        base_config['system'], system_config, node_config)

    client = SingleServiceClient(config_dict_system, args.service, args.service_config)

    if config_dict_system['general']['service_start_delay'] > 10:
        # wait a bit before trying to connect (spread out the system load)
        delay_val = random.randint(1, config_dict_system['general']['service_start_delay'] - 8)
    else:
        # eMews not configured for a service start delay, or delay is too small
        delay_val = 1

    client_wait.wait(delay_val)

    client.start()


if __name__ == '__main__':
    main()
