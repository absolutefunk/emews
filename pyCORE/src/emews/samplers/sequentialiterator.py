'''
Sequentual Iterator: iterates through a range of numbers, returning the
next number in a sequence (sequential)

Created on Feb 26, 2018

@author: Brian Ricks
'''
from emews.base.exceptions import KeychainException
import emews.samplers.valuesampler

class SequentualIterator(emews.samplers.valuesampler.ValueSampler):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(SequentualIterator, self).__init__(config)

        try:
            self._start_value = self.parameters.get('start_value')
            self._end_value = self.parameters.get('end_value')
        except KeychainException as ex:
            self.logger.error(ex)
            raise

        self._current_value = self._start_value

    def next_value(self):
        '''
        Contract from ValueSampler
        Returns the next value sequentially from a list
        '''
        if self._current_value < self._end_value:
            self._current_value += 1

        return self._current_value

    def update_parameters(self, **kwargs):
        '''
        @Override updates some or all parameters
        '''
        if 'start_value' in kwargs:
            self._start_value = kwargs.pop('start_value')
        if 'end_value' in kwargs:
            self._end_value = kwargs.pop('end_value')

        for key, _ in kwargs:
            self.logger.debug("Unknown parameter '%s' passed.  Ignoring ...", key)

        self.reset()

    def reset(self):
        '''
        @Override resets to the start value
        '''
        self._current_value = self._start_value
