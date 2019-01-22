"""
Samples from a bounded uniform distribution,  inclusive [lower_bound, upper_bound].

Created on Feb 26, 2018
@author: Brian Ricks
"""
import random

import emews.components.samplers.basesampler


class UniformSampler(emews.components.samplers.basesampler.BaseSampler):
    """classdocs."""

    __slots__ = ('lower_bound', 'upper_bound')

    def __init__(self, config):
        """Constructor."""
        super(UniformSampler, self).__init__()
        self.upper_bound = config['upper_bound']
        self.lower_bound = config['lower_bound']

    def update_sampler(self):
        """@Override Not needed."""
        pass

    def sample(self):
        """@Override samples using a bounded uniform distribution."""
        return random.randint(self.lower_bound, self.upper_bound)
