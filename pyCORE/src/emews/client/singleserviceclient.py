'''
Client for requesting services to spawn in emews.  Sends a single request per invocation.

Created on Apr 26, 2018
@author: Brian Ricks
'''
import argparse
import os
import signal
import socket

import emews.base.baseobject
import emews.base.config
import emews.base.exceptions
import emews.base.ihandlerclient
import emews.base.netclient

class SingleServiceClient(emews.base.BaseObject, emews.base.ihandlerclient.IHandlerClient):
    '''
    classdocs
    '''
    def __init__(self, config, command_tuple):
        '''
        Constructor
        command_tuple contains the service name and possible service config path
        '''
        client_config = config.clone_with_dict(config.extract_with_key('listener', 'config'))
        self._netclient = emews.base.netclient.NetClient(client_config, self)
        self._command_tuple = command_tuple  # contains service name / service config path

        # required params
        try:
            self._recv_buf = client_config.get('receive_buffer')
        except emews.base.exceptions.KeychainException as ex:
            self.logger.error(ex)
            raise

        self._stage = 0  # keeps track of where we are in the flow

    def start(self):
        '''
        Starts the client.
        '''
        self._netclient.start()

    def handle_readable_socket(self, sock):
        '''
        Given a socket, read its contents and act accordingly.
        '''
        try:
            # TODO: abstract this out into a 'StringNetClient', in which strings instead of socks
            # are passed.  Then we can do things like assemble chunks and pass them to this handler
            chunk = sock.recv(self._recv_buf)
        except socket.error as ex:
            self.logger.error(
                "Service '%s': socket error when receiving emews daemon message: %s",
                self._command_tuple[0], ex)
            self._netclient.stop()
            return

        if chunk == 'OK\n':
            if self._stage == 0:
                # initial response from emews daemon
                self._netclient.request_write(sock)
                self._stage += 1
                return
            elif self._stage == 1:
                # response from sent command
                self.logger.info("Service '%s': spawn command successful.", self._command_tuple[0])
                self._netclient.stop()
                return
        elif chunk == 'ERR\n':
            if self._stage == 0:
                # initial response from emews daemon
                self.logger.error("Service '%s': initial response from emews daemon was ERR.",
                                  self._command_tuple[0])
            elif self._stage == 1:
                # response from sent command
                self.logger.error("Service '%s': spawn command sent but received ERR.",
                                  self._command_tuple[0])

            self._netclient.stop()
            return
        else:
            self.logger.error("Service '%s': invalid response from emews daemon: %s",
                              self._command_tuple[0], chunk)
            self._netclient.stop()

    def handle_writable_socket(self, sock):
        '''
        Given a socket, write something to it or perform some other action.
        '''
        if self._stage != 1:
            self.logger.error("Service '%s': writable socket handler invoked on wrong stage.",
                              self._command_tuple[0])
            self._netclient.stop()
            return

        command_str = "S " + self._command_tuple[0]
        if self._command_tuple[1] is not None:
            command_str += " " + self._command_tuple[1]

        sock.sendall(command_str)

def main():
    '''
    main function
    '''
    parser = argparse.ArgumentParser(description='emews single service client')
    parser.add_argument("-s", "--sys_config", help="path of the emews system config file "\
    "(default: emews root)")
    parser.add_argument("-c", "--service_config", help="path of the service config file"\
    "(default: standard path and name)")
    parser.add_argument("service", help="name of the service class to load")
    args = parser.parse_args()

    logger = None
    def shutdown_signal_handler(signum, frame):
        '''
        Called when a registered signal is caught (ctrl-c for example).
        Relays to running service to gracefully shutdown.
        '''

        logger.info("Caught signal %s, shutting down service.", signum)

    # register signals (this is done in ConnectionManager if running the emews daemon)
    signal.signal(signal.SIGHUP, shutdown_signal_handler)
    signal.signal(signal.SIGINT, shutdown_signal_handler)

    sys_config_path = os.path.join(os.path.dirname(emews.version.__file__), "system.yml")\
                                   if args.sys_config is None else args.sys_config
    service_config_path = args.service_config  # if this is none, default will be attempted

    config = emews.base.config.Config('<none>', sys_config_path)  # node name not needed

    client = SingleServiceClient(config, (args.service, service_config_path))
    client.start()
