"""
Manages the eMews daemon execution.

Created on June 8, 2018
@author: Brian Ricks
"""
import collections
import signal
import threading

import emews.base.connectionmanager
import emews.base.logger
import emews.base.netclient
import emews.base.sysprop
import emews.base.thread_dispatcher
import emews.services.servicebuilder


class SystemManager(object):
    """Classdocs."""

    __slots__ = ('logger',
                 'sys'
                 '_config',
                 '_thread_dispatcher',
                 '_connection_manager',
                 '_net_client',
                 '_interrupted',
                 '_local_event')

    def __init__(self, config, sysprop):
        """
        Constructor.

        If local mode is true, then all distributed functionality is disabled.  This means that only
        the startup services will launch, and only local logging.  Local mode is useful for testing
        new services, or eMews itself.
        """
        super(SystemManager, self).__init__()

        self.logger = emews.base.logger.get_logger()

        # register signals
        signal.signal(signal.SIGHUP, self._shutdown_signal_handler)
        signal.signal(signal.SIGINT, self._shutdown_signal_handler)

        self.sys = sysprop
        self._config = config
        self._thread_dispatcher = None
        self._connection_manager = None
        self._net_client = None
        self._interrupted = False
        self._local_event = threading.Event()

        self.logger.info("[Network node] name: %s, node id: %d",
                         self.sys.node_name, self.sys.node_id)

        if self.sys.local:
            self.logger.info("Running in local mode.")

    def _startup_services(self):
        """Look in the config object to obtain any services present."""
        startup_services = self._config['startup_services']
        if len(startup_services) == 1:
            self.logger.info("1 startup service.")
        else:
            self.logger.info("%s startup services.", str(len(startup_services)))

        service_builder = emews.services.servicebuilder.ServiceBuilder(_inject={'sys': self.sys})

        for service_name in startup_services:
            # services may have parameters, or just the service name
            service_parameters = None
            if isinstance(service_name, collections.Mapping):
                # a dict can only contain one service
                if len(service_name) != 1:
                    err_str = "(startup services) Multiple services found in single " \
                              "dictionary.  Check either a system or node configuration " \
                              "file for a missing '-' prepending a service entry."
                    self.logger.error(err_str)
                    raise AttributeError(err_str)
                service_parameters = service_name.values()[0]
                service_name = service_name.keys()[0]

                self.logger.debug("Service '%s' has parameters defined in the configuration.",
                                  service_name)
            self.logger.debug("Dispatching service '%s' ...", service_name)

            self._thread_dispatcher.dispatch(service_builder.build(
                service_name, service_config_dict=service_parameters))

    def _shutdown_signal_handler(self, signum, frame):
        """Signal handler for incoming signals (those which may imply we need to shutdown)."""
        self.logger.info("Received signum %d, beginning shutdown...", signum)
        self._interrupted = True
        self._local_event.set()
        self.shutdown()

    def start(self):
        """Start the daemon."""
        self.logger.debug("Starting system manager ...")

        # instantiate thread dispatcher and connection manager
        self._thread_dispatcher = emews.base.thread_dispatcher.ThreadDispatcher(
            self._config['general'], _inject={'sys': self.sys})

        if self.sys.local:
            # local mode:  do not start ConnectionManager
            # SysProp object does not contain methods only available in non-local mode, such as
            # net methods.
            self._startup_services()
            if self._thread_dispatcher.count == 0:
                self.logger.info("No services running, nothing to do, shutting down ...")
                return

            self.logger.info("Waiting while services are running ...")

            while not self._interrupted and self._thread_dispatcher.count > 0:
                self._local_event.wait(1)

            if self._thread_dispatcher.count == 0:
                self.logger.info("No services running.")

        else:
            self._connection_manager = emews.base.connectionmanager.ConnectionManager(
                self._config['communication'], _inject={'sys': self.sys})
            self._net_client = emews.base.netclient.NetClient(
                self._config['communication'],
                self._config['hub']['node_address'],
                _inject={'sys': self.sys})

            # finish building sysprop
            self._finish_sysprop()

            # launch services and start the daemon's connection manager
            self._startup_services()
            self._connection_manager.start()  # blocks here

        self.logger.info("Shutdown complete.")

    def shutdown(self):
        """Shut down daemon operation."""
        if not self.sys.local:
            self._connection_manager.stop()

        # shut down any dispatched threads that may be running
        self._thread_dispatcher.shutdown_all_threads()

    def _finish_sysprop(self):
        """
        Finish building the SysProp object.

        This needs to be called before services are launched.
        """
        self.sys.net.hub_query = self._net_client.hub_query
        self.sys.net._ro = True
        self.sys._ro = True
