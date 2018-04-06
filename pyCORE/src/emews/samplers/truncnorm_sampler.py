'''
Created on Feb 26, 2018

@author: Brian Ricks
'''

from scipy.stats import truncnorm
import emews.common.value_sampler

class TruncnormSampler(emews.common.value_sampler.ValueSampler):
    '''
    classdocs
    '''

    def __init__(self, upper_bound, sigma):
        '''
        Constructor
        Class fields are declared here for readability
        '''
        self._lower_bound = 0
        self._upper_bound = None
        self._mu = None
        self._sigma = None

        self.update_parameters(upper_bound, sigma)

    def next_value(self):
        '''
        samples using a truncated normal distribution
        '''
        # print "Upper_bound: " + str(self._upper_bound) + " Mu: " + str(self._mu) + \
        # " Sigma: " + str(self._sigma)

        dist = truncnorm(
            (self._lower_bound - self._mu) / self._sigma, \
            (self._upper_bound - self._mu) / self._sigma, loc=self._mu, scale=self._sigma)

        return int(round(dist.rvs(1)[0]))

    def update_parameters(self, *args):
        '''
        updates parameters:
        args[0]=self._upper_bound
        args[1]=self._sigma
        '''
        if len(args) != 2:
            raise IndexError("[TruncnormSampler - update_parameters]: args count must equal 2")

        if args[0] is None or not isinstance(args[0], int) or args[0] < 0:
            raise ValueError("[TruncnormSampler - update_parameters]: \
                    upper_bound must be a positive int")
        self._upper_bound = args[0]
        if args[1] is None or \
                (not isinstance(args[1], float) and not isinstance(args[1], int)) or \
                args[1] < 0:
            raise ValueError("[TruncnormSampler - update_parameters]: \
                    sigma must be a positive int or float")
        self._sigma = args[1]

        self._mu = self._upper_bound / 2.0
