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
import emews.base.enums
import emews.services.baseservice


class BaseAgent(emews.services.baseservice.BaseService):
    """Classdocs."""

    __slots__ = ('_net_client', '_client_session', '_env_id', '_proto')

    def __init__(self):
        """Constructor."""
        super(BaseAgent, self).__init__()

        self._proto = self._net_client.protocols[emews.base.enums.net_protocols.NET_AGENT]

        self._client_session = self._net_client.create_client_session(
            emews.base.enums.net_protocols.NET_AGENT)  # NetClient session
        self._env_id = self._get_env_id()

    def _get_env_id(self):
        """Get the id of the environment for this agent."""
        env_id = self._net_client.client_session_get(
            self._client_session,
            self._proto[emews.base.enums.agent_protocols.AGENT_ENV_ID],
            [self.service_name.rpartition('_')[0]]
            )

        self.logger.debug("%s: assigned agent environment id: %d", self.service_name, env_id)

        return env_id

    def ask(self, key):
        """
        Ask (sense) the environment, returning evidence given a key.

        Evidence is a list of integers.
        """
        ev_str = self._net_client.client_session_get(
            self._client_session,
            self._proto[emews.base.enums.agent_protocols.AGENT_ASK],
            [self._env_id, key]
            )

        if ev_str == '0':
            return []

        val_str_list = ev_str.split(',')
        val_int_list = []
        for val_str in val_str_list:
            try:
                val_int_list.append(int(val_str))
            except TypeError:
                self.logger.warning(
                    "%s: the evidence string returned has a malformed value '%s' for key: %s",
                    self.service_name, val_str, key)
                return []

        return val_int_list

    def tell(self, obs_key, obs_val):
        """
        Tell (update) the environment with given observation K/V.

        Observations are provided to the environment, and is used to produce evidence.
        """
        if obs_key is None or obs_key == '':
            self.logger.error("%s: state key passed is empty.", self.service_name)
            raise ValueError("%s: state key passed is empty." % self.service_name)

        ack_val = self._net_client.client_session_get(
            self._client_session,
            self._proto[emews.base.enums.agent_protocols.AGENT_TELL],
            [self._env_id, obs_key, obs_val]
            )

        if ack_val != emews.base.enums.net_state.STATE_ACK:
            raise ValueError("%s: NACK returned when providing evidence (TELL)." % self.service_name)
