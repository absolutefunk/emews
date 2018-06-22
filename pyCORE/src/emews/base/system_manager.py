'''
Manages the eMews daemon execution.
'''
import emews.base.baseobject
import emews.base.exceptions
import emews.base.thread_dispatcher
import emews.services.servicebuilder

class SystemManager(emews.base.baseobject.BaseObject):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(SystemManager, self).__init__(config)
        self.logger.info("Starting system manager ...")

        # handles thread spawning/management
        self._thread_dispatcher = emews.base.thread_dispatcher.ThreadDispatcher(self.config)

        # start any services specified
        self._startup_services()





        self.logger.info("eMews daemon started.")

    def _startup_services(self):
        '''
        Looks in the config object to obtain any services present.
        '''
        startup_services = self.config.get_base("startup_services")
        self.logger.debug("%s startup services.", str(len(startup_services)))
        if startup_services is not None:
            for service_str, options in startup_services:
                self.logger.debug("Starting service '%s' ...", service_str)
                service_builder = emews.services.servicebuilder.ServiceBuilder(self.config)
                service_builder.service(service_str)

                if options is None:
                    service_config_path = None
                else:
                    service_config_path = options.get('config_path', None)

                service_builder.config_path(service_config_path)
                self._thread_dispatcher.dispatch_thread(service_builder.result, force_start=True)

    def shutdown(self):
        '''
        Shuts down daemon operation.
        '''

        # shut down any dispatched threads that may be running
        self._thread_dispatcher.shutdown_all_threads()
