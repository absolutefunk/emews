"""
Module for eMews services which act as agents.

Agent services interact with their environment, using eMews as an oracle.

Created on Mar 28, 2019
@author: Brian Ricks
"""
import emews.services.baseservice


class BaseAgent(emews.services.baseservice.BaseService):
    """Classdocs."""

    class Environment(object):
        """Container for environment methods."""

        __slots__ = ()

        def sense(self, context):
            """
            Sense the environment, returning an environment state.

            Environmental 'sensing' is accomplished by asking eMews what the environment looks like
            given some context, such as a webpage and other state.
            """
            return None

    __slots__ = ('_environment')

    def __init__(self, config):
        """Constructor."""
        super(BaseAgent, self).__init__()

        self._environment = self.Environment()

    @property
    def environment(self):
        """Return the Environment object for calling environment methods."""
        return self._environment
