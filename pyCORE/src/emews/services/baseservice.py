'''
Base class for emews services.
While this class is abstract, it still inherits the IService interface.  This is mainly to
separate base service functionality from the service decorators, which would be redundant otherwise.
Also instantiating decorators would be awkward if the base decorator had to call the BaseService
contructor.

Services must be in their own module, with the service name the same as the module name (service
name can use upper CamelCase - ServiceName for example).  This is so the string name passed to
build the appropriate service can also perform module lookup.

Created on Mar 5, 2018
@author: Brian Ricks
'''
from abc import abstractmethod
from threading import Event

import emews.base.baseobject
import emews.base.config
import emews.services.iservice

class BaseService(emews.base.baseobject.BaseObject, emews.services.iservice.IService):
    '''
    classdocs
    '''
    # config dependency injection pre-__init__
    # derive new type to get around meta conflict between the injector and ABCMeta
    __metaclass__ = type('BaseServiceMeta',
        (type(emews.services.iservice.IService), emews.base.config.InjectionMeta), {})
    __slots__ = ('_di_config', '_name', '_service_interrupt_event', '_interrupted')

    def __init__(self):
        '''
        Constructor
        '''
        # self._config and self._helpers are injected by the metaclass before __init__ is invoked
        super(BaseService, self).__init__()

        self._service_interrupt_event = Event()  # used to interrupt Event.wait() on stop()
        self._interrupted = False  # set to true on stop()

    @property
    def config(self):
        '''
        Returns the config object.
        '''
        return self._di_config

    @property
    def name(self):
        '''
        Returns the service's name.
        '''
        return self._name

    @property
    def interrupted(self):
        '''
        Returns true if the service has been interrupted (requested to stop).  Uses events.
        '''
        return self._interrupted

    def sleep(self, time):
        '''
        @Override Wraps the event.wait().  Convenience method.
        '''
        if self._interrupted:
            return

        self.logger.debug("%s sleeping for %s seconds.", self.name, time)
        self._service_interrupt_event.wait(time)

    @abstractmethod
    def run_service(self):
        '''
        Where the service entrance code goes.  Must be implemented by child class.
        '''
        pass

    def start(self):
        '''
        @Override Starts the service.
        '''
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
        '''
        @Override Gracefully exit service
        '''
        self._service_interrupt_event.set()
        self._interrupted = True
