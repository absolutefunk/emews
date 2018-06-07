'''
Samples from a bounded unform distribution,  inclusive [lower_bound, upper_bound].

Created on Feb 26, 2018
@author: Brian Ricks
'''
import random

from emews.base.exceptions import KeychainException
import emews.samplers.valuesampler

class UniformSampler(emews.samplers.valuesampler.ValueSampler):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        Class fields are declared here for readability
        '''
        super(UniformSampler, self).__init__(config)

        try:
            self._lower_bound = self.parameters.get('lower_bound')
            self._upper_bound = self.parameters.get('upper_bound')
        except KeychainException as ex:
            self.logger.error(ex)
            raise

    @property
    def next_value(self):
        '''
        @Override samples using a bounded uniform distribution
        '''
        return random.randint(self._lower_bound, self._upper_bound)

    def update_parameters(self, **kwargs):
        '''
        @Override updates some or all parameters
        '''
        if 'lower_bound' in kwargs:
            self._lower_bound = kwargs.pop('lower_bound')
        if 'upper_bound' in kwargs:
            self._upper_bound = kwargs.pop('upper_bound')

        for key, _ in kwargs:
            self.logger.debug("Unknown parameter '%s' passed.  Ignoring ...", key)

    def reset(self):
        '''
        @Override Resets to the start values.  Currently not implemented.
        '''
        raise NotImplementedError("Sampler currently does not support resetting parameters.")
