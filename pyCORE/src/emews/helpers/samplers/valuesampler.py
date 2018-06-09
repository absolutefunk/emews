'''
ValueSampler: Abstract class for samplers.  These are classes which usually
represent some distribution in which we can sample values from.

Created on Feb 26, 2018
@author: Brian Ricks
'''
from abc import abstractmethod, abstractproperty

from emews.base.exceptions import KeychainException
import emews.base.baseobject

class ValueSampler(emews.base.baseobject.BaseObject):
    '''
    classdocs
    '''
    def __init__(self, config):
        super(ValueSampler, self).__init__(config)

        try:
            # Pull parameters from config object being passed up, as self.config will not reference
            # this.
            self._parameters = config.get('parameters')
        except KeychainException:
            self._parameters = None
            self._logger.debug("Sampler does not have a 'parameters' section defined.")

        # parameter checks
        if self._parameters is not None:
            for key, value in self._parameters:
                if value is None:
                    # Nothing wrong with this per se, but it usually means that the parameter needs
                    # to be set to an actual value at some point (using update_parameters()).
                    self._logger.debug("Sampler parameter '%s' is None (null).", key)

    @abstractproperty
    def next_value(self):
        '''
        Returns the next value.
        '''
        pass

    @property
    def parameters(self):
        '''
        Returns the parameters of this sampler.
        '''
        return self._parameters

    @abstractmethod
    def update_parameters(self, **kwargs):
        '''
        Updates parameters for use with sampling.  Provides a way to do this
        after object instantiation.  kwargs allows for partial parameter updates.
        '''
        pass

    @abstractmethod
    def reset(self):
        '''
        Resets parameters to some initial value.
        '''
        pass
