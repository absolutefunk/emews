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
import sys

import emews.base.config
from emews.base.connectionmanager import ConnectionManager
from emews.version import __version__

def main():
    '''
    main function
    '''
    # Get the config file path
    # argv[1] = node name
    # argv[2] = conf file path (including filename)
    if len(sys.argv) != 3:
        print "Usage: %s <node_name> <config_file>\nwhere <config_file> is the path "\
              "(including filename) of the emews daemon config file." % sys.argv[0]
        return

    try:
        config = emews.config.Config(sys.argv[1], sys.argv[2])
    except StandardError as ex:
        print ex
        return

    logger = config.logger

    logger.debug("conf path: %s", emews.config.prepend_path(sys.argv[2]))
    logger.info("emews %s", __version__)

    # TODO: Add a base class for all classes which use the logger/config, and pass the sys_config
    # to its constructor, with properties for logger and config
    connection_manager = ConnectionManager(config)
    connection_manager.start()

    logger.info("emews shutdown")

if __name__ == '__main__':
    main()
