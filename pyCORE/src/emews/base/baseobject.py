'''
BaseObject: Convenience class that provides system properties as fields.  Enables consistency from
derived classes by providing a common methodology of system property access using self.

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
        # Object properties
        self._logger = emews.base.config.get_system_property('logger')

        # check if system properties have been updated more than expected
        if emews.base.config.get_system_property('update') > emews.base.config.EXPECTED_UPDATES:
            self._logger.error("System Properties have been updated unexpectedly!")

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
