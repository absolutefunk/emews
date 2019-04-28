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
import emews.base.enums
import emews.services.baseservice


class BaseAgent(emews.services.baseservice.BaseService):
    """Classdocs."""

    __slots__ = ('_net_client', '_client_session', '_env_id')

    def __init__(self):
        """Constructor."""
        super(BaseAgent, self).__init__()

        self._client_session = None  # session id for our session with the hub node
        self._env_id = None  # id for the environment we will interact with

    def _register_env_context(self, env_context):
        """Register the given env_context with the hub node."""
        pass

    def ask(self, env_context, state_key):
        """
        Ask (sense) the environment 'env_context', returning an environment state.

        Each call to ask will query the hub node.
        """
        while not self._interrupted and self._client_session is None:
            self._client_session = self._net_client.connect_node()

        if self._env_id is None:
            self._register_env_context(env_context)

        state_val = self._net_client.node_query(
            self._client_session,
            emews.base.enums.net_protocols.NET_AGENT,
            'HLH%ds' % len(state_key),
            [emews.base.enums.agent_protocols.AGENT_ASK, self._env_id, len(state_key), state_key])

    def tell(self, context, key, val):
        """
        Tell (update) and environment evidence key.

        Evidence is provided to the environment, and state is what is ultimately calculated from the
        given evidence.
        """
