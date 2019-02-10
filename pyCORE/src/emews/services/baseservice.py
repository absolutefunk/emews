"""
Base class for eMews services.

Services must be in their own module, with the service name the same as the module name (service
name can use upper CamelCase - ServiceName for example).  This is so the string name passed to
build the appropriate service can also perform module lookup.

Created on Mar 5, 2018
@author: Brian Ricks
"""
from abc import abstractmethod

import emews.base.meta
import emews.base.runnable


class BaseService(emews.base.runnable.Runnable):
    """Classdocs."""

    __metaclass__ = emews.base.meta.InjectionMetaWithABC
    __slots__ = ('service_name',
                 'service_id',
                 '_dispatcher',
                 '_service_loop',
                 'logger',
                 '_sys')

    @property
    def sys(self):
        """Return the system properties object."""
        return self._sys

    @property
    def looped(self):
        """Return if service is looped."""
        return self._service_loop is not None

    @abstractmethod
    def run_service(self):
        """Where the service entrance code goes.  Must be implemented by child class."""
        pass

    def start(self):
        """Start the service."""
        self.logger.debug("%s: starting [looped=%s].", self.service_name, self.looped)

        try:
            if self._service_loop is not None:
                # looped
                while not self.interrupted:
                    self.run_service()
                    self.sleep(self._service_loop.sample())
            else:
                self.run_service()
        except:  # noqa
            # We need to catch everything here so we can call the exit callback of our dispatcher
            # Don't worry, we reraise it.
            self.interrupt()
            self._dispatcher.cb_thread_exit(self, on_exception=True)
            raise

        self._dispatcher.cb_thread_exit(self)

    def stop(self):
        """Gracefully exit service."""
        if not self.interrupted:
            self.logger.debug("%s: stopping (requested) ...", self.service_name)
            self.interrupt()

    def register_dispatcher(self, dispatcher):
        """Register the exit function of the dispatcher handling this service."""
        self._dispatcher = dispatcher
        self.logger.debug("%s: dispatcher '%s' registered.", self.service_name, str(dispatcher))

    def __str__(self):
        """@Override print service name."""
        return self.service_name
