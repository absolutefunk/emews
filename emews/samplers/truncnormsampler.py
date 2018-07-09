'''
Centered positive truncated normal sampler.  Mu is defined as the median in
[lower_bound, upper_bound], and lower_bound = 0.

Created on Feb 26, 2018
@author: Brian Ricks
'''

from scipy.stats import truncnorm

import emews.base.exceptions
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

        self._lower_bound = 0
        self._upper_bound = None
        self._sigma = None

        self._dist = None  # distribution to sample from

        try:
            self.update_parameters(self.config.get('upper_bound'), self.config.get('sigma'))
        except emews.base.exceptions.MissingConfigException:
            self.logger.debug("Config empty, update_parameters must be called before next_value.")
        except emews.base.exceptions.KeychainException as ex:
            self.logger.error(ex)
            raise

    @property
    def next_value(self):
        '''
        samples using a truncated normal distribution
        '''
        return int(round(self._dist.rvs(1)[0]))

    def update_parameters(self, *args):
        '''
        updates parameters:
        args[0]=self._upper_bound
        args[1]=self._sigma

        Distribution is instantiated with new parameters here and cached.
        '''
        self._upper_bound = args[0]
        self._sigma = args[1]

        mu = self._upper_bound / 2.0

        self._dist = truncnorm(
            (self._lower_bound - mu) / self._sigma, \
            (self._upper_bound - mu) / self._sigma, loc=mu, scale=self._sigma)
