'''
BaseSampler: Abstract class for samplers.  These are classes which usually
represent some distribution in which we can sample values from.

Created on Feb 26, 2018
@author: Brian Ricks
'''
from abc import abstractmethod

import emews.base.baseobject
import emews.base.config

class BaseSampler(emews.base.baseobject.BaseObject):
    '''
    classdocs
    '''
    __metaclass_ = emews.base.config.InjectionMeta
    __slots__ = ('_di_config',)

    @property
    def config(self):
        '''
        Returns the config object.
        '''
        return self._di_config

    @abstractmethod
    def sample(self):
        '''
        Returns the next value sampled.
        '''
        pass

    @abstractmethod
    def update(self):
        '''
        Called by update_parameters after parameters have been updated.  Useful if model needs to be
        updated / reinstantiated.
        '''
        pass

    def update_parameters(self, **params):
        '''
        Given a dict of params, update the config.  Any missing keys will be copied from the
        current config.  Any keys passed to this method which are not in the original config will
        be ignored.
        '''
        self.update()
