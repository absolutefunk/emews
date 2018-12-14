"""
Manages the eMews daemon execution.

Created on June 8, 2018
@author: Brian Ricks
"""
import signal

import emews.base.baseobject
import emews.base.connectionmanager
import emews.base.exceptions
import emews.base.thread_dispatcher
import emews.services.servicebuilder


class SystemManager(emews.base.baseobject.BaseObject):
    """Classdocs."""

    def __init__(self, config, local_mode=False):
        """
        Constructor.

        If local_mode is true, then all distributed functionality is disabled.  This means that only
        the startup services will launch, and only local logging.  Local mode is useful for testing
        new services, or eMews itself.
        """
        super(SystemManager, self).__init__()

        self.logger.info("Running in local mode ...")

        # register signals
        signal.signal(signal.SIGHUP, self._shutdown_signal_handler)
        signal.signal(signal.SIGINT, self._shutdown_signal_handler)

        self._config = config
        self._local_mode = local_mode
        self._thread_dispatcher = None
        self.connection_manager = None

    def _startup_services(self):
        """Look in the config object to obtain any services present."""
        startup_services = self._config["startup_services"]
        self.logger.debug("%s startup services.", str(len(startup_services)))
        if startup_services:
            for service_str, options in startup_services:
                self.logger.debug("Starting service '%s' ...", service_str)
                service_builder = emews.services.servicebuilder.ServiceBuilder()
                service_builder.service(service_str)

                if options is None:
                    service_config_path = None
                else:
                    service_config_path = options.get('config_path', None)

                service_builder.config_path(service_config_path)
                self._thread_dispatcher.dispatch_thread(service_builder.result, force_start=True)

    def _shutdown_signal_handler(self, signum, frame):
        """Signal handler for incoming signals (those which may imply we need to shutdown)."""
        self.logger.info("Received signum %d, beginning shutdown...", signum)
        self.shutdown()

    def start(self):
        """Start the daemon."""
        self.logger.debug("Starting system manager ...")

        # instantiate thread dispatcher and connection manager
        self._thread_dispatcher = emews.base.thread_dispatcher.ThreadDispatcher(
            self._config['general'])

        # start any services specified
        self._startup_services()

        if self._local_mode:
            # local mode:  do not start ConnectionManager
            # TODO: implement blocking here so start() does not exit
            pass
        else:
            self.connection_manager = emews.base.connectionmanager.ConnectionManager(
                self._config['communication'], self._thread_dispatcher)

            # start the connection manager
            self.connection_manager.start()

    def shutdown(self):
        """Shut down daemon operation."""
        self.connection_manager.stop()

        # shut down any dispatched threads that may be running
        self._thread_dispatcher.shutdown_all_threads()
