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

import emews.base.baseobject
import emews.base.config
import emews.base.irunnable


class BaseService(emews.base.baseobject.BaseObject, emews.base.irunnable.IRunnable):
    """Classdocs."""

    # config dependency injection pre-__init__
    # derive new type to get around meta conflict between the injector and ABCMeta
    __metaclass__ = type(
        'BaseServiceMeta', (type(emews.base.irunnable.IRunnable), emews.base.config.InjectionMeta),
        {})
    __slots__ = ('name', 'interrupted', '_service_interrupt_event')

    def __init__(self):
        """Constructor."""
        # self._config and self._helpers are injected by the metaclass before __init__ is invoked
        super(BaseService, self).__init__()

        self._service_interrupt_event = Event()  # used to interrupt Event.wait() on stop()
        self.interrupted = False  # set to true on stop()

    def sleep(self, time):
        """Block the service for the given amount of time (in seconds)."""
        if self._interrupted:
            return

        self.logger.debug("%s sleeping for %s seconds.", self.name, time)
        self._service_interrupt_event.wait(time)

    @abstractmethod
    def run_service(self):
        """Where the service entrance code goes.  Must be implemented by child class."""
        pass

    def start(self):
        """@Override (IRunnable) Start the service."""
        self.logger.debug("%s starting.", self.name)

        try:
            self.run_service()
        except Exception as ex:
            self.logger.error("%s terminated abruptly (exception: %s)", self.name, ex)
            raise

        if not self._interrupted:
            self.logger.debug("%s stopping (finished)...", self.name)
        else:
            self.logger.debug("%s stopping (requested) ...", self.name)

    def stop(self):
        """@Override (IRunnable) Gracefully exit service."""
        self._service_interrupt_event.set()
        self._interrupted = True
