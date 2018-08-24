'''
BaseObject: the base of everything (well, almost...)

Created on Apr 9, 2018

@author: Brian Ricks
'''
import emews.base.config

class BaseObject(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        # object properties
        # system-wide logger
        self._logger = emews.base.config.get_system_property('logger')
        # name of the network node this object is constructed on
        self._node_name = emews.base.config.get_system_property('node_name')
    '''
    Object properties
    '''
    @property
    def logger(self):
        '''
        Returns the logger object.
        '''
        return self._logger

    @property
    def node_name(self):
        '''
        Returns the node name.
        '''
        return self._node_name
