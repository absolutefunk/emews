"""
Module for eMews services which act as agents.

Agent services interact with their environment, using eMews as an oracle.

Created on Mar 28, 2019
@author: Brian Ricks
"""
import emews.base.basehandler
import emews.services.baseservice


class BaseAgent(emews.services.baseservice.BaseService):
    """Classdocs."""

    __slots__ = ('_env_state')

    def __init__(self):
        """Constructor."""
        super(BaseAgent, self).__init__()

        self._env_state = {}

    def ask(self, context):
        """
        Ask (sense) the environment, returning an environment state.

        The environment state is cached here, pushed by the hub when it receives updates.  Each
        context refers to a specific environment which we are subscribed to.
        """
        return self._env_state.get(context, {})

    def tell(self, context, key, val):
        """
        Tell (update) the environment to a new state (k/v).

        The context is the specific environment in which to update.  We must be subscribed to the
        environment for any updates we give to be stored.
        """
