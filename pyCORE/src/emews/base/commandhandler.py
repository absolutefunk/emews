'''
Handles client command processing and service spawning.  Instantiations of this class invoked by
a ClientSession, which itself handles the communication between emews and a client.

Created on Apr 6, 2018

@author: Brian Ricks
'''
import emews.base.baseobject
from emews.services.servicebuilder import ServiceBuilder

class CommandException(Exception):
    '''
    Raised if a problem arises with a given command.
    '''
    pass

class CommandHandler(emews.base.baseobject.BaseObject):
    '''
    classdocs
    '''
    def __init__(self, config, thread_dispatcher):
        '''
        Constructor
        '''
        super(CommandHandler, self).__init__(config)
        # currently supported commands
        self._COMMAND_MAPPING = {
            'S': self.__do_makeservice,  # add a service
            'E': self.__do_exit,         # exit
        }

        self._thread_dispatcher = thread_dispatcher

    def process(self, cmd_tuple):
        '''
        Processes the command that the line represents.  If this is an exit command, return
        true, otherwise false.
        '''
        #TODO: generalize (commands) to services with cmdline args
        service_arg = None if len(cmd_tuple) == 2 else cmd_tuple[2]
        service_cfg_str = "<none>" if service_arg is None else cmd_tuple[2]
        self.logger.debug("Command: %s, Arg: %s, %s", cmd_tuple[0], cmd_tuple[1], service_cfg_str)

        if not cmd_tuple[0] in self._COMMAND_MAPPING:
            self.logger.warning("Command '%s' not recognized.", cmd_tuple[0])
            raise CommandException("Client command %s not recognized." % cmd_tuple[0])

        return self._COMMAND_MAPPING[cmd_tuple[0]](cmd_tuple[1], service_config_path=service_arg)

    def __do_makeservice(self, service_str, service_config_path=None):
        '''
        Attempts to create a Service from the service_str.  If a config_path for the service is
        given, then use that for service configuration.
        '''
        service_builder = ServiceBuilder(self.config)
        #try:
        service_builder.service(service_str)
        service_builder.config_path(service_config_path)
        service_instance = service_builder.result
        '''except StandardError:
            # throw exception so client knows this failed
            self.logger.error("Could not build service '%s' from client input.", service_str)
            raise CommandException("Could not build service '%s' from client input." % service_str)'''

        self._thread_dispatcher.dispatch_thread(service_instance)
        return True

    def __do_exit(self, arg_str):
        '''
        Exits the underlying ClientSession (terminate connection with client).
        '''
        self.logger.debug("Exit command processed.")
        return False
