"""
Manages the eMews daemon execution.

Created on June 8, 2018
@author: Brian Ricks
"""
import collections
import ipaddress
import signal
import threading

import emews.base.handler_logging
import emews.base.sysprop
import emews.base.thread_dispatcher
import emews.services.servicebuilder


class SystemManager(object):
    """Classdocs."""

    __slots__ = ('logger',
                 'sys',
                 '_sysprop_dict'
                 '_config',
                 '_thread_dispatcher',
                 '_connection_manager',
                 '_interrupted',
                 '_local_event',
                 '_hub_addr')

    def __init__(self, config, sysprop_dict):
        """
        Constructor.

        If local mode is true, then all distributed functionality is disabled.  This means that only
        the startup services will launch, and only local logging.  Local mode is useful for testing
        new services, or eMews itself.
        """
        super(SystemManager, self).__init__()

        self.logger = sysprop_dict['logger']

        # register signals
        signal.signal(signal.SIGHUP, self._shutdown_signal_handler)
        signal.signal(signal.SIGINT, self._shutdown_signal_handler)

        self._sysprop_dict = sysprop_dict
        self._config = config
        self._sys = None  # will contain the sysprop object once created
        self._thread_dispatcher = None
        self._connection_manager = None
        self._interrupted = False
        self._local_event = threading.Event()
        self._hub_addr = None  # will contain the hub node's IP address if not running in local mode

        self.logger.info("[Network node] name: %s, node id: %d",
                         self._sys.node_name, self._sys.node_id)

        if self._sysprop_dict['local']:
            self.logger.info("Running in local mode.")

    def _startup_services(self):
        """Look in the config object to obtain any services present."""
        startup_services = self._config['startup_services']
        if len(startup_services) == 1:
            self.logger.info("1 startup service.")
        else:
            self.logger.info("%s startup services.", str(len(startup_services)))

        service_builder = emews.services.servicebuilder.ServiceBuilder(self._sys)

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
            self._config['general'], self._sysprop_dict)

        if self._sysprop_dict['local']:
            # local mode:  do not start ConnectionManager
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
                self._config['communication'], self._sysprop_dict)

            if self._sysprop_dict['is_hub']:
                self.logger.info("This node is the hub.")
                # add distributed logging listener
                self._connection_manager.add_listener(
                    self._config['logging']['port'],
                    emews.base.handler_logging.HandlerLogging)

            # cache the hub node's network address
            hub_addr = self._config['hub']['node_addr']
            if hub_addr is None:
                # TODO: implement hub node address broadcasting to other nodes
                raise NotImplementedError(
                    "Hub broadcast not implemented yet.  Please define hub address in config.")

            self._hub_addr = ipaddress.IPv4Address(hub_addr)

            self._build_sysprop()
            self._startup_services()

            self._connection_manager.set_sys(self.sys)
            self._connection_manager.start()  # blocks here

        self.logger.info("Shutdown complete.")

    def shutdown(self):
        """Shut down daemon operation."""
        if not self._sys.local:
            self._connection_manager.stop()

        # shut down any dispatched threads that may be running
        self._thread_dispatcher.shutdown_all_threads()

    # sysprop methods
    def _build_sysprop(self):
        """Build the sysprop object."""
        if not self._sysprop_dict['local']:
            self._sysprop_dict['hub_address'] = self._get_hub_addr
        else:
            self._sysprop_dict['hub_address'] = self._local_ret

        self.sys = emews.base.sysprop.SysProp(self._sysprop_dict)
        self._sysprop_dict = None

    def _local_ret(self):
        """Use for sysprop methods that are not supported in local mode."""
        self.logger.debug("This method is not supported in local mode.")
        return None

    def _get_hub_addr(self, query):
        """Return the hub node's network address."""
        return self._hub_addr
