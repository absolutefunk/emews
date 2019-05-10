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

        self._client_session = self._net_client.create_client_session()  # NetClient session
        self._env_id = {}  # [env_context] = env_id

    def _get_env_id(self, env_context):
        """Get the id of the env_context from the hub node.  Env id must already exist."""
        env_id = self._net_client.client_session_get(
            self._client_session,
            emews.base.enums.net_protocols.NET_AGENT,
            emews.base.enums.agent_protocols.AGENT_ENV_ID,
            env_context,
            )

        if env_id == 0:
            self.logger.error("Invalid environment id returned (0).  Is the env_context registered?")
            raise ValueError("Invalid environment id returned (0).  Is the env_context registered?")

    def ask(self, env_context, state_key):
        """
        Ask (sense) the environment 'env_context', returning an environment state.

        Each call to ask will query the hub node.
        """
        if state_key is None or state_key == '':
            self.logger.error("%s: state key passed is empty.", self.service_name)
            raise ValueError("%s: state key passed is empty." % self.service_name)

        if env_context not in self._env_id:
            env_id = self._get_env_id(env_context)
            self._env_id[env_context] = env_id

        state_val = self._net_client.client_session_get(
            self._client_session,
            emews.base.enums.net_protocols.NET_AGENT,
            [
                (emews.base.enums.agent_protocols.AGENT_ASK, 'H'),
                (self._env_id, 'L'),
                (state_key, 's')
            ]
            )

        return state_val

    def tell(self, env_context, state_key, state_val):
        """
        Tell (update) and environment evidence key.

        Evidence is provided to the environment, and state is what is ultimately calculated from the
        given evidence.
        """
        if state_key is None or state_key == '':
            self.logger.error("%s: state key passed is empty.", self.service_name)
            raise ValueError("%s: state key passed is empty." % self.service_name)

        if env_context not in self._env_id:
            env_id = self._get_env_id(env_context)
            self._env_id[env_context] = env_id
