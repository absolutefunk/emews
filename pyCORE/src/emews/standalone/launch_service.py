'''
Standalone launcher for services.  Launches services independent of emews.  Note that not all
services can be launched this way; services with emews dependencies outside of basic configuration
and logging will need to be launched through emews.

Created on Apr 11, 2018

@author: Brian Ricks
'''
import argparse

import emews.base.config
import emews.services.servicebuilder

def main():
    '''
    main function
    '''
    parser = argparse.ArgumentParser(description='Emews standalone service launcher.')
    parser.add_argument("-s", "--sys_config", help="path of the emews system config file "\
    "(default: emews root)")
    parser.add_argument("-c", "--service_config", help="path of the service config file")
    parser.add_argument("service", help="name of the service class to load")
    args = parser.parse_args()

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
        raise
        return

    service_instance.start()

if __name__ == '__main__':
    main()
