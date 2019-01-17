'''
Base class for emews service decorators (modifiers).
Subclasses when overriding the required methods can use super(cls, self) to access the methods
being overridden.

Created on Mar 30, 2018
@author: Brian Ricks
'''
import emews.base.baseobject
import emews.base.irunnable

class ServiceModifier(emews.base.baseobject.BaseObject, emews.base.irunnable.IRunnable):
    '''
    classdocs
    '''
    __metaclass__ = type(
        'ServiceModifierMeta',
        (type(emews.services.iservice.IService), emews.base.config.InjectionMeta), {})
    __slots__ = ('_recipient_service', '_ph')

    def __init__(self):
        '''
        Constructor
        '''
        # self._config and self._helpers are injected by the metaclass before __init__ is invoked
        super(ServiceModifier, self).__init__()

        # TODO: evaluate performance for services with many modifiers. Large function call chains
        # may cause significant slowdown.

        # NOTE: Placeholder instance variable to appease pylint.  When aggregating types, like above
        # for the metaclasses, and if no instance variables are defined here, pylint throws an error
        # that this is an old-style class .  I'm not sure if the error is legit (doubtful), so this
        # will do until python 3 porting time.
        self._ph = None

    @property
    def interrupted(self):
        '''
        @Override Returns true if the service has been interrupted (requested to stop).
        Use implementaton from recipient_service.
        '''
        return self._recipient_service.interrupted

    def sleep(self, time):
        '''
        Call the sleep implementaton of recipient_service.
        '''
        self._recipient_service.sleep(time)

    def start(self):
        '''
        @Override (IRunnable) Starts the service.
        '''
        self._recipient_service.start()

    def stop(self):
        '''
        @Override (IRunnable) Gracefully exit service
        '''
        self._recipient_service.stop()
