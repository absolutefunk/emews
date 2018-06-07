'''
Centered positive truncated normal sampler.  Mu is defined as the median in
[lower_bound, upper_bound], and lower_bound = 0.

Created on Feb 26, 2018
@author: Brian Ricks
'''

from scipy.stats import truncnorm

from emews.base.exceptions import KeychainException
import emews.samplers.valuesampler

class TruncnormSampler(emews.samplers.valuesampler.ValueSampler):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        Class fields are declared here for readability
        '''
        super(TruncnormSampler, self).__init__(config)

        self._upper_bound = None
        self._sigma = None

        try:
            self._upper_bound = self.parameters.get('upper_bound')
            self._sigma = self.parameters.get('sigma')
        except KeychainException as ex:
            self.logger.error(ex)
            raise

        self._lower_bound = 0

        if self._upper_bound is not None and self._sigma is not None:
            mu = self._upper_bound / 2.0
            self._dist = truncnorm(
                (self._lower_bound - mu) / self._sigma, \
                (self._upper_bound - mu) / self._sigma, loc=mu, scale=self._sigma)
        else:
            self.logger.debug("One or more parameters is None (null).  "\
                "Must update these parameters before calling next_value().")

    @property
    def next_value(self):
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

    def reset(self):
        '''
        @Override Resets to the start values.  Currently not implemented.
        '''
        raise NotImplementedError("Sampler currently does not support resetting parameters.")
