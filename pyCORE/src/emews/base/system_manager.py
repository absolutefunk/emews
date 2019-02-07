"""
Manages the eMews daemon execution.

Created on June 8, 2018
@author: Brian Ricks
"""
import collections
import signal

# import emews.base.connectionmanager
import emews.base.thread_dispatcher
import emews.services.servicebuilder
import emews.sys


class SystemManager(object):
    """Classdocs."""

    __slots__ = ('_config', '_thread_dispatcher', 'connection_manager')

    def __init__(self, config):
        """
        Constructor.

        If local mode is true, then all distributed functionality is disabled.  This means that only
        the startup services will launch, and only local logging.  Local mode is useful for testing
        new services, or eMews itself.
        """
        super(SystemManager, self).__init__()

        # register signals
        signal.signal(signal.SIGHUP, self._shutdown_signal_handler)
        signal.signal(signal.SIGINT, self._shutdown_signal_handler)

        self._config = config
        self._thread_dispatcher = None
        self.connection_manager = None

        emews.sys.logger.info("Network node: %s, node id: %d",
                              emews.sys.node.name, emews.sys.node.id)

        if emews.sys.local:
            emews.sys.logger.info("Running in local mode.")

    def _startup_services(self):
        """Look in the config object to obtain any services present."""
        startup_services = self._config['startup_services']
        if len(startup_services) == 1:
            emews.sys.logger.info("1 startup service.")
        else:
            emews.sys.logger.info("%s startup services.", str(len(startup_services)))

        for service_name in startup_services:
            # services may have parameters, or just the service name
            if isinstance(service_name, collections.Mapping):
                # a dict can only contain one service
                if len(service_name) != 1:
                    err_str = "(startup services) Multiple services found in single " \
                              "dictionary.  Check either a system or node configuration " \
                              "file for a missing '-' prepending a service entry."
                    emews.sys.logger.error(err_str)
                    raise AttributeError(err_str)
                s_dict = service_name.values()[0]
                service_name = service_name.keys()[0]

                if not isinstance(s_dict, collections.Mapping):
                    # formatting issue in the config
                    err_str = "(startup services) Service '%s' is defined in a dictionary, but " \
                              "does not contain a valid parameters dictionary."
                    emews.sys.logger.error(err_str, service_name)
                    raise AttributeError(err_str % service_name)
                service_parameters = service_name.values()[0]['parameters']
                emews.sys.logger.debug("Service '%s' has parameters defined in the configuration.",
                                       service_name)
            emews.sys.logger.debug("Dispatching service '%s' ...", service_name)

            # TODO: support config path or even config KVs in startup_services
            self._thread_dispatcher.dispatch_thread(
                emews.services.servicebuilder.ServiceBuilder.build(service_name), force_start=False)

    def _shutdown_signal_handler(self, signum, frame):
        """Signal handler for incoming signals (those which may imply we need to shutdown)."""
        emews.sys.logger.info("Received signum %d, beginning shutdown...", signum)
        self.shutdown()

    def start(self):
        """Start the daemon."""
        emews.sys.logger.debug("Starting system manager ...")

        # instantiate thread dispatcher and connection manager
        self._thread_dispatcher = emews.base.thread_dispatcher.ThreadDispatcher(
            self._config['general'])

        # start any services specified
        self._startup_services()

        if emews.sys.local:
            # local mode:  do not start ConnectionManager
            if self._thread_dispatcher.count == 0:
                emews.sys.logger.info("No services started, nothing to do, shutting down ...")
                self.shutdown()
                return

            # Need to block here if any services are running.
            self._thread_dispatcher.join()

        else:
            self.connection_manager = emews.base.connectionmanager.ConnectionManager(
                self._config['communication'], self._thread_dispatcher)
            self.connection_manager.start()

    def shutdown(self):
        """Shut down daemon operation."""
        if not emews.sys.local:
            self.connection_manager.stop()

        # shut down any dispatched threads that may be running
        self._thread_dispatcher.shutdown_all_threads()
