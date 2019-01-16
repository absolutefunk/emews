'''
Samples from a bounded unform distribution,  inclusive [lower_bound, upper_bound].

Created on Feb 26, 2018
@author: Brian Ricks
'''
import random

import emews.helpers.requires.samplers.basesampler

class UniformSampler(emews.helpers.requires.samplers.basesampler.BaseSampler):
    '''
    classdocs
    '''
    __slots__ = ()

    def sample(self):
        '''
        @Override samples using a bounded uniform distribution
        '''
        return random.randint(self.config.lower_bound, self.config.upper_bound)

    def update(self):
        '''
        @Override invoked after parameters are updated.
        '''
        pass
