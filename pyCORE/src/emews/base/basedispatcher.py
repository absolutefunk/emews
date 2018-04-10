'''
Base class for Dispatchers.  A Dispatcher dispatches an event to all callbacks subscribed to it.

The implementation departs a bit from the traditional observer pattern:
- As everything basically is a first class object in python, observers are callables (methods, etc),
so callbacks in this contexts are not the entire objects, but rather callables from the objects.
This allows the updates on callbacks to pass the callables directly, so all the callbacks have to do
is invoke them (ie, no code to figure out what the event was and what to do)
- Events are strings which allow the Dispatcher to map events to callables.  The dispatcher doesn't
care what the callable actually is, it simply makes the assumption that the callable can take the
args passed along with it during dispatch calls.
- This implementation does not require an interface for a listener, as the callbacks are invoked
directly.

Overall this should be a pretty efficient implementation.

Created on Apr 8, 2018

@author: Brian Ricks
'''
import emews.base.baseobject

class BaseDispatcher(emews.base.baseobject.BaseObject):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(BaseDispatcher, self).__init__(config)

        # An event is a key in the dict, and for each event, a set is stored of the callbacks
        # subscribed to the event.
        self._subscribed_callbacks = {}

    def dispatch(self, event, *args):
        '''
        Dispatches dispatched_event to all its callbacks.
        '''
        for callback in self._subscribed_callbacks[event]:
            try:
                callback(*args)
            except TypeError as ex:
                self.logger.warning("Callback %s could not be invoked: %s", callback.__name__, ex)

    def subscribe(self, event, callback):
        '''
        Registers (subscribes) the passed callback to the given event.
        '''
        if not event in self._subscribed_callbacks:
            # create the event list
            self._subscribed_callbacks[event] = set()

        self._subscribed_callbacks[event].add(callback)
        self.logger.debug("Callback %s subscribed to event %s.", callback.__name__, event)

    def unsubscribe(self, event, callback):
        '''
        Removes (unsubscribes) the passed callback from the given event.
        '''
        if not event in self._subscribed_callbacks:
            self.logger.warning("Event %s not present, cannot unsubscribe callback %s.",
                                event, callback.__name__)
            return

        try:
            self._subscribed_callbacks[event].remove(callback)
        except KeyError:
            self.logger.warning("Callback %s is not subscribed to event %s, cannot unsubscribe.",
                                callback.__name__, event)
