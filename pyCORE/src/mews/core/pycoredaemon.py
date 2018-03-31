'''
Driver for running pyCORE services.

Because each node in an emulation environment is assumed to be contained (ie,
each node has its own process space and network stack), the daemon would need
to be spawned once per node.  Once the daemon process is started, pyCORE services
are spawned as threads.  This way the resource footprint is minimized per node,
as in addition to the resources saved by having one process for all services,
other aspects (such as logging and control of services) is shared among all
service threads.

Created on Mar 24, 2018

@author: Brian Ricks
'''

import ConfigParser
import logging
import logging.config
import sys

import mews.core.config
from mews.core.servicemanager import ServiceManager
from mews.core.version import __version__

def main():
    '''
    main function
    '''

    # Get the config file path
    # argv[1] = node name
    # argv[2] = conf file path (including filename)
    if len(sys.argv) != 3:
        print "Usage: %s <node_name> <config_file>\nwhere <config_file> is the path "\
              "(including filename) of the pyCORE daemon config file." % sys.argv[0]
        return

    try:
        config = mews.core.config.Config(sys.argv[1], mews.core.config.prepend_path(sys.argv[2]))
    except ConfigParser.ParsingError as ex:
        print ex
        return

    # setup logging (this will affect all child loggers)
    # Here we pass a dictionary to the logger for initial configuration, then
    # setup a LoggerAdapter so we can log the Node name (hostname) to the log
    # entries without appending it to the message each time.
    logging.config.dictConfig(config.logconfig)
    logger = logging.getLogger(config.logbase)

    logger.debug("conf path: %s", mews.core.config.prepend_path(sys.argv[2]))
    logger.info("MEWS pyCORE %s", __version__)

    service_manager = ServiceManager(config)
    service_manager.start()

    logger.info("pyCORE shutdown")

if __name__ == '__main__':
    main()
