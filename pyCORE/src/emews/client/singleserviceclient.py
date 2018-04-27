'''
Client for requesting services to spawn in emews.  Sends a single request per invocation.

Created on Apr 26, 2018
@author: Brian Ricks
'''
import argparse
import os
import signal

import emews.base.config

def main():
    '''
    main function
    '''
    parser = argparse.ArgumentParser(description='emews standalone service launcher')
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
