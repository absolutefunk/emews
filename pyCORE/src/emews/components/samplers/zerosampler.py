"""
Just returns zero.

Created on Feb 8, 2019
@author: Brian Ricks
"""
import emews.components.samplers.basesampler


class ZeroSampler(emews.components.samplers.basesampler.BaseSampler):
    """classdocs."""

    __slots__ = ()

    def __init__(self, config):
        """Constructor."""
        super(ZeroSampler, self).__init__()

    def update_sampler(self):
        """@Override Not needed."""
        pass

    def sample(self):
        """@Override samples using a bounded uniform distribution."""
        return 0
