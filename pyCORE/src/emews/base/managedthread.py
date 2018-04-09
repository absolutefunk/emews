'''
Decorator for BaseThread which provides support for management using ServiceManager.
Currently extended by ServiceThread and ListenerThread.

Created on Apr 8, 2018

@author: Brian Ricks
'''
import emews.base.ilistener
import emews.base.thread_decorator

class ManagedThread(emews.base.thread_decorator.ThreadDecorator, emews.base.ilistener.IListener):
    '''
    classdocs
    '''
    def __init__(self, recipient_thread, cb_registration):
        '''
        cb_registration is the callback for registering this object to the ServiceManager.  While
        the ServiceManager could simply register this object itself when instantiating it, this
        method enforces that at least a registration callback will be invoked during construction.
        Using a callback also loosens coupling as compared to passing the ServiceManager object
        itself and calling some register method (which would most likely be this callback, except
        now we don't need to know the name of it or anything, and no other methods of the
        ServiceManager are known to us - ie, no additional dependencies can form).
        '''
        super(ManagedThread, self).__init__(recipient_thread)

    def update_listener(self, dispatched_event):
        '''
        @Override from IListener
        Called from a dispatcher when an event is dispatched.  In this case, the dispatcher should
        be the service manager or some delegate on its behalf telling us what we should do.
        '''
