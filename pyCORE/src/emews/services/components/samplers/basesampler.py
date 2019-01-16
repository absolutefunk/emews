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
    __slots__ = ()

    @abstractmethod
    def sample(self):
        '''
        Returns the next value sampled.
        '''
        pass

    def update(self, **params):
        '''
        Updates parameters of the model.
        '''
        for param, val in params:
            try:
                setattr(self, param, val)
            except AttributeError:
                self.logger.debug("Ignoring parameter '%s', which does not exist.")
                continue
