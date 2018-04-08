'''
Handles client command processing and service spawning.  Instantiations of this class invoked by
a ListenerThread, which itself handles the communication between emews and a client.

Created on Apr 6, 2018

@author: Brian Ricks
'''
from emews.services.servicebuilder import ServiceBuilder

class ClientCommandException(Exception):
    '''
    Raised if a problem arises with a given command.
    '''
    pass

class ClientHandler(object):
    '''
    classdocs
    '''
    def __init__(self, sys_config):
        '''
        Constructor
        '''
        # currently supported commands
        self._COMMAND_MAPPING = {
            'S': self.__do_makeservice,  # add a service
            'E': self.__do_exit,         # exit
        }

        self._sys_config = sys_config
        self._logger = self.config.logger

    @property
    def logger(self):
        '''
        returns the logger object
        '''
        return self._logger

    @property
    def config(self):
        '''
        returns the system configuration object
        '''
        return self._sys_config

    def process(self, cmd_tuple):
        '''
        Processes the command that the line represents.  If this is an exit command, return
        true, otherwise false.
        '''
        #TODO: generalize (commands) to services with cmdline args
        self.logger.debug("Command: %s, Arg: %s", cmd_tuple[0], cmd_tuple[1])

        if not cmd_tuple[0] in self._COMMAND_MAPPING:
            self.logger.warning("Command %s not recognized.", cmd_tuple[0])
            raise ClientCommandException("Command %s not recognized." % cmd_tuple[0])

        return self._COMMAND_MAPPING[cmd_tuple[0]](cmd_tuple[1])

    def __do_makeservice(self, service_str, service_config_path=None):
        '''
        Attempts to create a Service from the service_str.  If a config_path for the service is
        given, then use that for service configuration.
        '''
        service_builder = ServiceBuilder(self.config)
        try:
            service_builder.service(service_str)
            service_builder.config_path(service_config_path)
            service_instance = service_builder.result
        except StandardError:
            # We still return true so other commands can be processed
            self.logger.error("Could not build service %s from client input.", service_str)

        return True

    def __do_exit(self, arg_str):
        '''
        Exit the listener.
        '''
        self.logger.debug("Exit command processed.")
        return False
