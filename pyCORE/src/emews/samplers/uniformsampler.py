'''
Created on Feb 26, 2018

@author: Brian Ricks
'''

import random

import emews.samplers.valuesampler

class UniformSampler(emews.samplers.valuesampler.ValueSampler):
    '''
    classdocs
    '''

    def __init__(self, config):
        '''
        Constructor
        Class fields are declared here for readability
        '''
        super(UniformSampler, self).__init__(config)

        self._lower_bound = None
        self._upper_bound = None

        self.update_parameters(self.config.get('lower_bound'), self.config.get('upper_bound'))

    def next_value(self):
        '''
        @Override samples using a bounded uniform distribution
        '''

        return random.randint(self._lower_bound, self._upper_bound)

    def update_parameters(self, *args):
        '''
        @Override updates parameters:
        args[0]=self._lower_bound
        args[1]=self._upper_bound
        '''

        self._upper_bound = args[0]
        self._upper_bound = args[1]

    def reset(self):
        '''
        Resets the sampler.  Here we reset the parameters to what they were on instantiation.
        '''
        self._lower_bound = self.config.get('lower_bound')
        self._upper_bound = self.config.get('upper_bound')
