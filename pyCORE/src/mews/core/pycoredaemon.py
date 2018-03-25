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
import os
import sys

from mews.core.logconf import log_config
from mews.core.servicespawner import ServiceSpawner
from mews.core.version import __version__

class BaseConfig(object):
    '''
    parses and stores the pyCORE config
    '''

    def __init__(self, filename):
        '''
        Constructor
        '''
        # class fields
        self._nodesection = "general"
        self._nodekey = "nodename"
        self._nodename = None
        self._config = ConfigParser.SafeConfigParser()

        self.parse(filename)

    def parse(self, filename):
        '''
        parse the config file
        '''
        #print filename
        try:
            with open(filename) as f:
                self._config.readfp(f)
        except IOError as ex:
            print "Could not open configuration file.\n%s" % ex
            return
        except ConfigParser.Error as ex:
            print "Error while parsing configuration file.\n%s" % ex
            f.close()
            return

        f.close()

        # now check for the proper section and key
        try:
            self._nodename = self._config.get(self._nodesection, self._nodekey)
        except ConfigParser.Error as ex:
            print "Error while assigning node name\n%s" % ex
            return

    @property
    def nodename(self):
        '''
        Returns the node name.
        This field is treated a bit differently from the rest as the logger
        queries this function to obtain the node name for each log output, so
        the lookup needs to be fast (ie, no dictionary).
        '''
        return self._nodename

    def get_value(self, section, key):
        '''
        Given a valid section and key, returns its value.
        Note, this will throw an exception if the section or key does not exist
        '''
        return self._config.get(section, key)

def prepend_path(filename):
    '''
    Prepends an absolute path to the filename, relative to the directory this
    module was loaded from.
    '''
    path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    return os.path.join(path, filename)

def main():
    '''
    main function
    '''

    # Get the config file path
    if len(sys.argv) != 2:
        print "Usage: %s <config_file>\nwhere <config_file> is the path "\
              "(including filename) of the pyCORE daemon config file." % sys.argv[0]
        return

    config = BaseConfig(prepend_path(sys.argv[1]))
    if config.nodename is None:
        # node name was never assigned, so just return
        return

    # setup logging (this will affect all child loggers)
    # Here we pass a dictionary to the logger for initial configuration, then
    # setup a LoggerAdapter so we can log the Node name (hostname) to the log
    # entries without appending it to the message each time.
    log_config['formatters']['default']['format'] = \
    log_config['formatters']['default']['format'].replace(
        '<NodeName>', (log_config['formatters']['default']['nodename-format'] % config.nodename))
    logging.config.dictConfig(log_config)
    logger = logging.getLogger('pyCore.base')

    logger.info("MEWS pyCORE %s", __version__)

if __name__ == '__main__':
    main()
