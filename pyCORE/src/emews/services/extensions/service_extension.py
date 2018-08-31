'''
Base class for emews service decorators (extensions).
Subclasses when overriding the required methods can use super(cls, self) to access the methods
being overridden.

Created on Mar 30, 2018
@author: Brian Ricks
'''
import emews.base.baseobject
import emews.base.config
import emews.services.iservice

class ServiceExtension(emews.base.baseobject.BaseObject, emews.services.iservice.IService):
    '''
    classdocs
    '''
    __metaclass__ = type(
        'ServiceExtensionMeta',
        (type(emews.services.iservice.IService), emews.base.config.InjectionMeta), {})
    __slots__ = ('_config', '_helpers', '_recipient_service')

    def __init__(self):
        '''
        config: decorator config
        recipient_service: previous decorator in the chain (or service if root of chain)
        '''
        # self._config and self._helpers are injected by the metaclass before __init__ is invoked
        super(ServiceExtension, self).__init__()

        self._recipient_service = None  # set during _post_init

    def _post_init(self, recipient_service):
        '''
        Dependency injection for setting recipient service (either the base service or another
        decorator in a chain). Invoked by ServiceBuilder.
        '''
        # pre-_init dependency injection is not needed here as the recipient service is instantiated
        # first.
        self._recipient_service = recipient_service

    @property
    def config(self):
        '''
        Returns the config object.
        '''
        return self._config

    @property
    def helpers(self):
        '''
        Returns the helpers object.
        '''
        return self._helpers

    @property
    def interrupted(self):
        '''
        @Override Returns true if the service has been interrupted (requested to stop).
        Use implementaton from recipient_service.
        '''
        return self._recipient_service.interrupted

    def sleep(self, time):
        '''
        @Override calls the sleep implementaton of recipient_service.
        '''
        self._recipient_service.sleep(time)

    def start(self):
        '''
        @Override Starts the service.
        '''
        self._recipient_service.start()

    def stop(self):
        '''
        @Override Gracefully exit service
        '''
        self._recipient_service.stop()
