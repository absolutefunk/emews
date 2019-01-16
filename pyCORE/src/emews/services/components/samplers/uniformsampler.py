'''
Samples from a bounded unform distribution,  inclusive [lower_bound, upper_bound].

Created on Feb 26, 2018
@author: Brian Ricks
'''
import random

import emews.services.components.samplers.basesampler

class UniformSampler(emews.services.components.samplers.basesampler.BaseSampler):
    '''
    classdocs
    '''

    def sample(self):
        '''
        @Override samples using a bounded uniform distribution
        '''
        return random.randint(self.lower_bound, self.upper_bound)
