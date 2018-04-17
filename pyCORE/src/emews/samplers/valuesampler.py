'''
ValueSampler: Abstract class for samplers.  These are classes which usually
represent some distribution in which we can sample values from.

Created on Feb 26, 2018
@author: Brian Ricks
'''
from abc import abstractmethod, abstractproperty

import emews.base.baseobject

class ValueSampler(emews.base.baseobject.BaseObject):
    '''
    classdocs
    '''
    def __init_(self, config):
        super(ValueSampler, self).__init(config)

    @abstractproperty
    def next_value(self):
        '''
        Returns the next value.
        '''
        pass

    @abstractmethod
    def reset(self):
        '''
        Resets the sampler.
        '''
        pass

    @abstractmethod
    def update_parameters(self, *args):
        '''
        Updates parameters for use with sampling.  Provides a way to do this
        after object instantiation.
        '''
        pass
