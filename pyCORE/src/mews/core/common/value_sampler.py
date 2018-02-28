'''
ValueSampler: Abstract class for samplers.  These are classes which usually
represent some distribution in which we can sample values from.

Created on Feb 26, 2018

@author: Brian Ricks
'''

from abc import abstractmethod

class ValueSampler(object):
    '''
    classdocs
    '''

    @abstractmethod
    def next_value(self):
        '''
        Returns the next value.
        Required to be implemented in a child class.
        '''
        raise NotImplementedError("Must implement in subclass.")

    def reset(self):
        '''
        Resets the sampler.
        This method should be overridden in a child class if required.
        '''
        pass

    def update_parameters(self, *args):
        '''
        Updates parameters for use with sampling.  Provides a way to do this
        after object instantiation.
        This method should be overridden in a child class if required.
        '''
        pass
