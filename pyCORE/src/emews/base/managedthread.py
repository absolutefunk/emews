'''
Decorator for BaseThread which provides support for management using ServiceManager.
Currently extended by ServiceThread and ListenerThread.

Created on Apr 8, 2018

@author: Brian Ricks
'''
import emews.base.thread_decorator

class ManagedThread(emews.base.thread_decorator.ThreadDecorator):
    '''
    classdocs
    '''
