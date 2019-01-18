"""
Iterates through a range of numbers, returning the next number in a sequence.

Once the last value in the sequence is sampled, that value is returned until the parameters are
updated, at which point the sequence resets according to the new parameters.

Created on Feb 26, 2018

@author: Brian Ricks
"""
import emews.services.components.samplers.basesampler


class SequentualIterator(emews.services.components.samplers.basesampler):
    """Classdocs."""

    __slots__ = ('start_value', 'end_value', '_current_value')

    def __init__(self, config):
        """Constructor."""
        super(SequentualIterator, self).__init__()

        self.start_value = config['start_value']
        self.end_value = config['end_value']

        self._current_value = self.start_value

    def update_sampler(self):
        """@Override Reset sampler."""
        self._current_value = self.start_value

    def sample(self):
        """@Override Return the next value sequentially from a list."""
        if self._current_value < self.end_value:
            self._current_value += 1

        return self._current_value
