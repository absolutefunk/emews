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

    def __init__(self, lower_bound, upper_bound):
        '''
        Constructor
        Class fields are declared here for readability
        '''
        self._lower_bound = None
        self._upper_bound = None

        self.update_parameters(lower_bound, upper_bound)

    def next_value(self):
        '''
        samples using a bounded uniform distribution
        '''

        return random.randint(self._lower_bound, self._upper_bound)

    def update_parameters(self, *args):
        '''
        updates parameters:
        args[0]=self._lower_bound
        args[1]=self._upper_bound
        '''
        if len(args) != 2:
            raise IndexError("[UniformSampler - update_parameters]: args count must equal 2")

        if args[0] is None or not isinstance(args[0], int) or args[0] < 0:
            raise ValueError("[UniformSampler - update_parameters]: \
                    lower_bound must be a positive int")
        self._lower_bound = args[0]
        if args[1] is None or not isinstance(args[1], int) or args[1] < 0:
            raise ValueError("[UniformSampler - update_parameters]: \
                    upper_bound must be a positive int")
        self._upper_bound = args[1]
