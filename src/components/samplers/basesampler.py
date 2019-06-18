"""
BaseSampler: Abstract class for samplers.

These are classes which usually represent some distribution in which we can sample values from.

Created on Feb 26, 2018
@author: Brian Ricks
"""
from abc import abstractmethod

import emews.components.basecomponent


class BaseSampler(emews.components.basecomponent.BaseComponent):
    """classdocs."""

    __slots__ = ()

    @abstractmethod
    def sample(self):
        """Return the next value sampled."""
        pass

    @abstractmethod
    def update_sampler(self):
        """Update the sampler, given the new parameters.  Called by update()."""
        pass

    def update(self, **params):
        """Update parameters of the model."""
        if not params:
            self.logger.debug("Not invoking update_sampler(), as no parameters updated.")
            return

        for param, val in params.iteritems():
            try:
                setattr(self, param, val)
            except AttributeError:
                self.logger.debug("Ignoring parameter '%s', which does not exist.")
                continue

        self.update_sampler()
