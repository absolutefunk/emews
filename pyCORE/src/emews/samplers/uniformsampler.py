'''
Samples from a bounded unform distribution,  inclusive [lower_bound, upper_bound].

Created on Feb 26, 2018
@author: Brian Ricks
'''
import random

import emews.base.exceptions
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

        self._lower_bound = None
        self._upper_bound = None

        try:
            self.update_parameters(self.config.get('lower_bound'), self.config.get('upper_bound'))
        except emews.base.exceptions.MissingConfigException:
            self.logger.debug("Config empty, update_parameters must be called before next_value.")
        except emews.base.exceptions.KeychainException as ex:
            self.logger.error(ex)
            raise

    def next_value(self):
        '''
        @Override samples using a bounded uniform distribution
        '''
        return random.randint(self._lower_bound, self._upper_bound)

    def update_parameters(self, *args):
        '''
        @Override updates parameters:
        args[0]=self._lower_bound
        args[1]=self._upper_bound
        '''

        self._lower_bound = int(args[0])
        self._upper_bound = int(args[1])
