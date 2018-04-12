'''
Sequentual Iterator: iterates through a range of numbers, returning the
next number in a sequence (sequential)

Created on Feb 26, 2018

@author: Brian Ricks
'''

import emews.samplers.value_sampler

class SequentualIterator(emews.samplers.value_sampler.ValueSampler):
    '''
    classdocs
    '''

    def __init__(self, start_value, end_value):
        '''
        Constructor
        '''
        self._start_value = start_value
        self._end_value = end_value
        self._current_value = start_value

    def next_value(self):
        '''
        Contract from ValueSampler
        Returns the next value sequentially from a list
        '''
        if self._current_value < self._end_value:
            self._current_value += 1

        return self._current_value

    def reset(self):
        '''
        resets to the start value
        '''
        self._current_value = self._start_value
