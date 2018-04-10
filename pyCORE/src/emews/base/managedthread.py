'''
Decorator for BaseThread which provides support for management using a dispatcher.  Note that this
class is also a dispatcher, which is needed to dispatch events when it shuts down on its own.

Created on Apr 8, 2018

@author: Brian Ricks
'''
import emews.base.basedispatcher
import emews.base.thread_decorator

class ManagedThread(emews.base.thread_decorator.ThreadDecorator,
                    emews.base.basedispatcher.BaseDispatcher):
    '''
    The following events are used:
    thread_stopping: called when thread is stopping
    '''

    def __init__(self, recipient_thread, dispatcher_subscribe):
        '''
        dispatcher_subscribe is the dispatcher subscribe method in which we use to subscribe to its
        events.
        '''
        super(ManagedThread, self).__init__(recipient_thread)

        # subscribe to the dispatcher's 'stop_thread' event
        dispatcher_subscribe('stop_thread', self.stop)

    def stop(self):
        '''
        @Override Notify any callbacks subscribed that we are shutting down.
        '''

        self.dispatch('thread_stopping', self)
        super(ManagedThread, self).stop()
