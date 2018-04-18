'''
Standalone launcher for services.  Launches services independent of emews.  Note that not all
services can be launched this way; services with emews dependencies outside of basic configuration
and logging will need to be launched through emews.

Created on Apr 11, 2018

@author: Brian Ricks
'''
import argparse
import signal

import emews.base.config
import emews.services.servicebuilder

def main():
    '''
    main function
    '''
    parser = argparse.ArgumentParser(description='emews standalone service launcher')
    parser.add_argument("-s", "--sys_config", help="path of the emews system config file "\
    "(default: emews root)")
    parser.add_argument("-c", "--service_config", help="path of the service config file")
    parser.add_argument("service", help="name of the service class to load")
    args = parser.parse_args()

    service_instance = None
    def shutdown_signal_handler(signum, frame):
        '''
        Called when a registered signal is caught (ctrl-c for example).
        Relays to running service to gracefully shutdown.
        '''
        if service_builder is None:
            # interrupt occurred before servicebuilder instantiation
            print "Caught signal %s, shutting down." % signum
            return
        elif service_instance is None:
            # interrupt occurred before service instantiation
            print "Caught signal %s, shutting down." % signum
            service_builder.stop()
            return

        service_instance.logger.info("Caught signal %s, shutting down service.", signum)
        service_instance.stop()

    # register signals (this is done in ConnectionManager if running the emews daemon)
    signal.signal(signal.SIGHUP, shutdown_signal_handler)
    signal.signal(signal.SIGINT, shutdown_signal_handler)

    sys_config_path = "../system.yml" if args.sys_config is None else args.sys_config
    service_config_path = "../services/" + args.service.lower() + "/" + \
                          args.service.lower() + ".yml"

    print "emews standalone service launcher"
    print "  Using system config path: " + sys_config_path
    print "  Using service config path: " + service_config_path

    try:
        sys_config = emews.base.config.Config('standalone', sys_config_path)
    except StandardError as ex:
        print ex
        return

    try:
        service_builder = emews.services.servicebuilder.ServiceBuilder(sys_config)
        service_builder.service(args.service)
        service_builder.config_path(service_config_path)
        service_instance = service_builder.result
    except StandardError as ex:
        print ex
        return

    service_instance.logger.info("Starting service '%s'.", service_instance.__class__.__name__)
    service_instance.start()

if __name__ == '__main__':
    main()
