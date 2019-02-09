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
import emews.base.threading.runnable


class BaseService(emews.base.threading.runnable.Runnable):
    """Classdocs."""

    __metaclass__ = emews.base.meta.InjectionMetaWithABC
    __slots__ = ('service_name',
                 'service_id',
                 'logger',
                 '_sys')

    @property
    def sys(self):
        """Return the system properties object."""
        return self._sys

    @abstractmethod
    def run_service(self):
        """Where the service entrance code goes.  Must be implemented by child class."""
        pass

    def start(self):
        """Start the service."""
        self.logger.debug("%s starting.", self.service_name)

        try:
            self.run_service()
        except Exception as ex:
            self.logger.error("%s terminated abruptly (exception: %s)", self.service_name, ex)
            raise

        if not self.interrupted:
            self.logger.debug("%s stopping (finished)...", self.service_name)
        else:
            self.logger.debug("%s stopping (requested) ...", self.service_name)

    def stop(self):
        """Gracefully exit service."""
        self.interrupt()
