"""
Centered positive truncated normal sampler.

Mu is defined as the median in [lower_bound, upper_bound], and lower_bound = 0.

Created on Feb 26, 2018
@author: Brian Ricks
"""
from scipy.stats import truncnorm

import emews.services.components.samplers.basesampler


class TruncnormSampler(emews.services.components.samplers.basesampler.BaseSampler):
    """Classdocs."""

    __slots__ = ('lower_bound', 'upper_bound', 'sigma', '_dist')

    def __init__(self, config):
        """Constructor."""
        super(TruncnormSampler, self).__init__()
        self.upper_bound = config['upper_bound']
        self.sigma = config['lower_bound']

        self.lower_bound = 0

        if self.upper_bound is not None and self.sigma is not None:
            mu = self.upper_bound / 2.0
            self._dist = truncnorm((self.lower_bound - mu) / self.sigma,
                                   (self.upper_bound - mu) / self.sigma, loc=mu, scale=self.sigma)

    def sample(self):
        """Sample from a truncated normal distribution."""
        return int(round(self._dist.rvs(1)[0]))

    def update_sampler(self, **kwargs):
        """@Override re-instantiate distribution with new parameters."""
        mu = self.upper_bound / 2.0
        self._dist = truncnorm((self.lower_bound - mu) / self.sigma,
                               (self.upper_bound - mu) / self.sigma, loc=mu, scale=self.sigma)
