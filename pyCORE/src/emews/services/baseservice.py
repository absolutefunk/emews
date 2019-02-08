"""
Base class for eMews services.

While this class is abstract, it still inherits the IService interface.  This is mainly to
separate base service functionality from the service decorators, which would be redundant otherwise.
Also instantiating decorators would be awkward if the base decorator had to call the BaseService
contructor.

Services must be in their own module, with the service name the same as the module name (service
name can use upper CamelCase - ServiceName for example).  This is so the string name passed to
build the appropriate service can also perform module lookup.

Created on Mar 5, 2018
@author: Brian Ricks
"""
from abc import abstractmethod
from threading import Event

import emews.base.meta
import emews.base.irunnable


class BaseService(emews.base.irunnable.IRunnable):
    """Classdocs."""

    # TODO: test ABC to make sure unimplemented methods are actually being caught (note: this happens at instantiation time)
    __metaclass__ = emews.base.meta.InjectionMetaWithABC
    __slots__ = ('service_name',
                 'service_id',
                 'logger',
                 '_sys',
                 '_interrupted',
                 '_service_interrupt_event')

    def __init__(self):
        """Constructor."""
        super(BaseService, self).__init__()

        self._service_interrupt_event = Event()  # used to interrupt Event.wait() on stop()
        self._interrupted = False  # set to true on stop()

    def sleep(self, time):
        """Block the service for the given amount of time (in seconds)."""
        if self._interrupted:
            return

        self.logger.debug("%s sleeping for %s seconds.", self.service_name, time)
        self._service_interrupt_event.wait(time)

    @property
    def interrupted(self):
        """@Override Interrupted state of the service."""
        return self._interrupted

    @property
    def sys(self):
        """Return the system properties object."""
        return self._sys

    @abstractmethod
    def run_service(self):
        """Where the service entrance code goes.  Must be implemented by child class."""
        pass

    def start(self):
        """@Override (IRunnable) Start the service."""
        self.logger.debug("%s starting.", self.service_name)

        try:
            self.run_service()
        except Exception as ex:
            self.logger.error("%s terminated abruptly (exception: %s)", self.service_name, ex)
            raise

        if not self._interrupted:
            self.logger.debug("%s stopping (finished)...", self.service_name)
        else:
            self.logger.debug("%s stopping (requested) ...", self.service_name)

    def stop(self):
        """@Override (IRunnable) Gracefully exit service."""
        self._service_interrupt_event.set()
        self._interrupted = True
