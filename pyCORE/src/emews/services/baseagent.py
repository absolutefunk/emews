"""
Module for eMews services which act as agents.

Agent services interact with their environment, using eMews as an oracle.

Concepts:
- Evidence: K/Vs which agents tell to the environment
- State: K/Vs which the environment generate based on evidence
- Context: Environment context, or name, which groups evidence and state

Created on Mar 28, 2019
@author: Brian Ricks
"""
import emews.base.basehandler
import emews.services.baseservice


class BaseAgent(emews.services.baseservice.BaseService):
    """Classdocs."""

    __slots__ = ('_net_client')

    def __init__(self):
        """Constructor."""
        super(BaseAgent, self).__init__()

    def ask(self, context):
        """
        Ask (sense) the environment, returning an environment state.

        Each call to ask will query the hub node.
        """
        return

    def tell(self, context, key, val):
        """
        Tell (update) and environment evidence key.

        Evidence is provided to the environment, and state is what is ultimately calculated from the
        given evidence.
        """
