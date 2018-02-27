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
        returns the next value
        '''
        raise NotImplementedError("Must implement in subclass.")

    @abstractmethod
    def reset(self):
        '''
        resets the sampler
        '''
        raise NotImplementedError("Must implement in subclass.")
