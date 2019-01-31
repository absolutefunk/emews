"""
Manages the eMews daemon execution.

Created on June 8, 2018
@author: Brian Ricks
"""
import os
import select
import signal

import emews.base.baseobject
import emews.base.connectionmanager
import emews.base.exceptions
import emews.base.thread_dispatcher
import emews.services.servicebuilder


class SystemManager(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_config', '_thread_dispatcher', 'connection_manager', '_local_block_pipe')

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
        self._local_block_pipe = None  # if in local mode, will reference a pipe for blocking

        if self.sys['local']:
            self.logger.info("Running in local mode ...")

    def _startup_services(self):
        """Look in the config object to obtain any services present."""
        startup_services = self._config['startup_services']
        self.logger.info("%s startup services.", str(len(startup_services)))

        for service_str in startup_services:
            self.logger.debug("Dispatching service '%s' ...", service_str)

            # TODO: support config path or even config KVs in startup_services
            self._thread_dispatcher.dispatch_thread(
                emews.services.servicebuilder.ServiceBuilder.build(service_str), force_start=False)

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

        if self.sys['local']:
            # local mode:  do not start ConnectionManager
            # Need to block here, as otherwise this method will just return.
            r_pipe, w_pipe = os.pipe()
            self._local_block_pipe = (os.fdopen(r_pipe), os.fdopen(w_pipe, 'w'))
            try:
                r_pipes, _, e_pipes = select.select(
                    [self._local_block_pipe[0]], [], [self._local_block_pipe[0]])
            except select.error:
                self.logger.error("Select error while blocking.")
                raise

            for r_pipe in r_pipes:
                if r_pipe is self._local_block_pipe[0]:
                    self.logger.debug("Received data on block pipe, block released.")
                    self._local_block_pipe[0].close()
            for e_pipe in e_pipes:
                if e_pipe is self._local_block_pipe[0]:
                    self.logger.error("Block pipe in exceptional state, block released.")
                    self._local_block_pipe[0].close()
        else:
            self.connection_manager = emews.base.connectionmanager.ConnectionManager(
                self._config['communication'], self._thread_dispatcher)
            self.connection_manager.start()

    def shutdown(self):
        """Shut down daemon operation."""
        if not self.sys['local']:
            self.connection_manager.stop()

        # shut down any dispatched threads that may be running
        self._thread_dispatcher.shutdown_all_threads()

        if self.sys['local']:
            # release the block in start()
            self._local_block_pipe[1].write("E")
            self._local_block_pipe[1].close()
