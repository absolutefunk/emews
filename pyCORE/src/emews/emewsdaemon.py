'''
Driver for running emews services and other components.

Because each node in an emulation environment is assumed to be contained (ie,
each node has its own process space and network stack), the daemon would need
to be spawned once per node.  Once the daemon process is started, emews services
are spawned as threads.  This way the resource footprint is minimized per node,
as in addition to the resources saved by having one process for all services,
other aspects (such as logging and control of services) is shared among all
service threads.

Created on Mar 24, 2018

@author: Brian Ricks
'''
import argparse
import os

import emews.base.config
from emews.base.connectionmanager import ConnectionManager
import emews.version

def main():
    '''
    main function
    '''
    parser = argparse.ArgumentParser(description='emews network node daemon')
    parser.add_argument("-s", "--sys_config", help="path of the emews system config file "\
    "(default: emews root)")
    parser.add_argument("node_name", help="name of the node this daemon launches under")
    args = parser.parse_args()

    sys_config_path = os.path.join(os.path.dirname(emews.version.__file__), "system.yml")\
        if args.sys_config is None else args.sys_config

    print "emews %s" % emews.version.__version__
    print "  Using system config path: " + sys_config_path

    try:
        config = emews.base.config.Config(args.node_name, sys_config_path)
    except StandardError as ex:
        print ex
        return

    connection_manager = ConnectionManager(config)
    connection_manager.start()

    print "emews shutdown"

if __name__ == '__main__':
    main()
