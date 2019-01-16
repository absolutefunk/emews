'''
Centered positive truncated normal sampler.  Mu is defined as the median in
[lower_bound, upper_bound], and lower_bound = 0.

Created on Feb 26, 2018
@author: Brian Ricks
'''

from scipy.stats import truncnorm

from emews.base.exceptions import KeychainException
import emews.samplers.valuesampler

class TruncnormSampler(emews.services.components.samplers.basesampler.BaseSampler):
    '''
    classdocs
    '''
    __slots__ = ('lower_bound', 'upper_bound', 'sigma', '_dist')

    def __init__(self, config):
        """Constructor"""
        self.upper_bound = config['upper_bound']
        self.sigma = config['lower_bound']

        self.lower_bound = 0

        if self.upper_bound is not None and self.sigma is not None:
            mu = self.upper_bound / 2.0
            self._dist = truncnorm((self.lower_bound - mu) / self.sigma, \
                (self.upper_bound - mu) / self.sigma, loc=mu, scale=self.sigma)

    def sample(self):
        '''
        samples using a truncated normal distribution
        '''
        return int(round(self._dist.rvs(1)[0]))

    def update_parameters(self, **kwargs):
        '''
        @Override updates some or all parameters
        '''
        if 'upper_bound' in kwargs:
            self._upper_bound = kwargs.pop('upper_bound')
            mu = self._upper_bound / 2.0
        if 'sigma' in kwargs:
            self._sigma = kwargs.pop('sigma')

        for key, _ in kwargs:
            self.logger.debug("Unknown parameter '%s' passed.  Ignoring ...", key)

        # this is redundant if no parameters passed (method shouldn't be called in such case)
        self._dist = truncnorm(
            (self._lower_bound - mu) / self._sigma, \
            (self._upper_bound - mu) / self._sigma, loc=mu, scale=self._sigma)
