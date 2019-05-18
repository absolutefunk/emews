"""
Client for requesting services to spawn in eMews.  Sends a single request per invocation.

Created on Apr 26, 2018
@author: Brian Ricks
"""
import argparse
import os
import signal
import socket
import struct
import sys
import threading

import emews.base.config
import emews.base.enums


class SingleServiceClient(object):
    """Classdocs."""

    __slots__ = ('_port', '_service_name', '_service_config_path', '_connect_timeout')

    def __init__(self, config, service_name, service_config_path):
        """Constructor."""
        self._port = config['communication']['port']
        print "[service_launcher] daemon port: " + str(self._port)

        self._connect_timeout = config['communication']['connect_timeout']
        print "[service_launcher] connect timeout: " + str(self._connect_timeout)

        self._service_name = service_name
        print "[service_launcher] service name to request: " + self._service_name

        self._service_config_path = service_config_path
        if self._service_config_path is None:
            print "[service_launcher] service configuration path: <default>"
        else:
            print "[service_launcher] service configuration path: " + self._service_config_path

        sys.stdout.flush()

    def start(self):
        """Connect to eMews daemon and send command."""
        ack = None

        cmd_list = []
        cmd_list.append(emews.base.enums.net_protocols.NET_SPAWN)
        cmd_list.append(0)  # node id (clients don't have a node id, leave at zero)
        cmd_list.append(emews.base.enums.spawner_protocols.SPAWNER_LAUNCH_SERVICE)
        cmd_list.append(len(self._service_name))
        cmd_list.append(self._service_name)

        if self._service_config_path is None:
            struct_format = '>HLHL%dsL' % len(self._service_name)
            cmd_list.append(0)
        else:
            struct_format = '>HLHL%dsL%ds' % (len(self._service_name), len(self._service_config_path))
            cmd_list.append(len(self._service_config_path))
            cmd_list.append(self._service_config_path)

        try:
            try:
                print "[service_launcher] connecting ..."
                sys.stdout.flush()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self._connect_timeout)
                sock.connect(('127.0.0.1', self._port))
            except socket.error as ex:
                sock.close()
                raise IOError("socket error on connect: %s." % ex)

            print "[service_launcher] connected."
            sys.stdout.flush()

            try:
                sock.sendall(struct.pack(struct_format, *cmd_list))
            except socket.error as ex:
                sock.close()
                raise IOError("socket error on service launch request send: %s." % ex)

            print "[service_launcher] service launch request sent, waiting response ..."
            sys.stdout.flush()

            try:
                chunk = sock.recv(2)  # ACK (2 bytes)

                if not len(chunk):
                    sock.close()
                    raise IOError("connection reset by peer.")

                ack = struct.unpack('>H', chunk)[0]
            except socket.error as ex:
                sock.close()
                raise IOError("socket error on response: %s." % ex)
        except KeyboardInterrupt:
            try:
                # this may fail if socket endpoint is already closed
                sock.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass

            sock.close()
            raise

        try:
            # this most likely will fail as the hub node should have closed the connection
            sock.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass

        sock.close()

        if ack == emews.base.enums.net_state.STATE_NACK:
            raise IOError("Received NACK from eMews daemon.")

        print "[service_launcher] done."
        sys.stdout.flush()


def main():
    """Do setup and launch."""
    parser = argparse.ArgumentParser(description='eMews Service Launcher')
    parser.add_argument("-s", "--sys_config", help="path of the eMews system config file "
                        "(default: emews root)")
    parser.add_argument("-c", "--node_config", help="path of the eMews node-based config file "
                        "(default: <none>)")
    parser.add_argument("-p", "--service_config", help="path of the service config file"
                        "(default: standard path and name)")
    parser.add_argument("service", help="name of the service class to load")
    args = parser.parse_args()

    print "[service_launcher] eMews Service Launcher Client."
    sys.stdout.flush()

    client = None
    client_wait = threading.Event()

    def shutdown_signal_handler(signum, frame):
        """Handle when a registered signal is caught (ctrl-c for example)."""
        client_wait.set()
        client.interrupted = True

    signal.signal(signal.SIGHUP, shutdown_signal_handler)
    signal.signal(signal.SIGINT, shutdown_signal_handler)

    # config
    root_path = emews.base.config.get_root_path()
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

    start_delay = config_dict_system['client']['service_launch_delay']
    if start_delay > 0:
        print "[service_launcher] waiting for " + str(start_delay) + " seconds before connecting ..."
        sys.stdout.flush()
        client_wait.wait(start_delay)

    client.start()


if __name__ == '__main__':
    main()
