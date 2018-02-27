'''
Created on Feb 26, 2018

@author: Brian Ricks
'''

import scipy.stats

# constants
DEFAULT_TRUNCNORM_STDDEV = 0.2

def truncnorm_index(list_size, sigma=DEFAULT_TRUNCNORM_STDDEV):
    '''
    selects an index using a truncated normal distribution
    '''
    if sigma is None:
        raise ValueError("[truncnorm_index]: sigma of invalid type")

    mu = (list_size - 1) / 2.0  # pick the middle link to distribute around

    lower = 0  # lower bound
    upper = list_size - 1  # upper bound

    dist = scipy.stats.truncnorm(
        (lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)

    return int(round(dist.rvs(1)[0]))
