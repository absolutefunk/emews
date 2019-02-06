"""
Base class for emews service decorators (modifiers).

Subclasses when overriding the required methods can use super(cls, self) to access the methods
being overridden.

Created on Mar 30, 2018
@author: Brian Ricks
"""
import emews.base.baseobject
import emews.base.irunnable
import emews.base.meta


class ServiceModifier(emews.base.baseobject.BaseObject, emews.base.irunnable.IRunnable):
    """Classdocs."""

    __metaclass__ = type(
        'ServiceModifierMeta',
        (type(emews.base.irunnable.IRunnable), emews.base.meta.MetaInjection), {})
    __slots__ = ('_recipient_service')

    @property
    def interrupted(self):
        """
        @Override Interrupted state of the service.

        If a service is interrupted, it has been requested by eMews to terminate gracefully.  Use
        implementaton from recipient_service.
        """
        return self._recipient_service.interrupted

    def sleep(self, time):
        """Call the sleep implementaton of recipient_service."""
        self._recipient_service.sleep(time)

    def start(self):
        """@Override (IRunnable) Starts the service."""
        self._recipient_service.start()

    def stop(self):
        """@Override (IRunnable) Gracefully exit service."""
        self._recipient_service.stop()
