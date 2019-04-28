"""
Agent server.

Handles agent communication on the hub.

Created on Apr 3, 2019
@author: Brian Ricks
"""
import struct

import emews.base.enums
import emews.base.baseserv
import emews.base.queryserv


class ServAgent(emews.base.queryserv.QueryServ):
    """Classdocs."""

    __slots__ = ('_env_evidence', '_env_state', '_session_data', '_env_id_map', '_env_id')

    def __init__(self):
        """Constructor."""
        super(ServAgent, self).__init__()

        self.handlers = [None] * emews.base.enums.agent_protocols.ENUM_SIZE
        self.handlers[emews.base.enums.agent_protocols.AGENT_ASK] = \
            emews.base.baseserv.Handler(self._agent_ask_env_req, 'HHs', send_type_str='L')
        self._cb[emews.base.enums.agent_protocols.AGENT_TELL] = self._agent_tell_env_req
        self._cb[emews.base.enums.agent_protocols.AGENT_ENV_ID] = self._agent_env_reg_req

        self._session_data = {}

        self._env_evidence = []  # environment evidence cache
        self._env_state = []  # environment state cache
        self._env_evidence.append(None)  # env id 0 is invalid
        self._env_state.append(None)  # env id 0 is invalid
        self._env_id = 1

        self._env_map = {}  # env context to id mapping

    def env_register(self, from_env, env_context):
        """Register a new env context from an agent environment."""
        self._env_map[env_context] = self._env_id
        self._env_evidence.append({})  # dict for env evidence K/Vs at specific context
        self._env_state.append({})  # dict for env state K/Vs at specific context
        self.logger.info("Agent environment '%s' registered new env context '%s', assigned id: %d.",
                         from_env.__class__.__name__, env_context, self._env_id)

        self._env_id += 1

    def serv_init(self, node_id, session_id):
        """Init of new agent session."""
        pass

    def serv_close(self, session_id):
        """Close a session."""
        pass

    # agent ask
    def _agent_ask_env_req(self, session_id, env_id, state_key):
        """Remote agent wants a state key from the given env_id."""
        if env_id < 1 or env_id >= len(self._env_state):
            self.logger.warning("Session id: %d, env id '%d' not registered.",
                                session_id, env_id)
            return None

        state_val = self._env_state[env_id].get(state_key, None)

        if state_val is None:
            self.logger.warning("Session id: %d, env id: %d, state key '%s' does not exist.",
                                session_id, env_id, state_key)
            return None

        return (state_val, self.handlers[emews.base.enums.agent_protocols.AGENT_TELL])

    # agent tell
    def _agent_tell_env_req(self, session_id, env_id):
        """Agent is going to update an evidence key's value corresponding to the given env id."""
        if env_id < 1 or env_id >= len(self._env_evidence):
            self.logger.warning("Session id: %d, env id '%d' not registered.",
                                session_id, env_id)
            return None

        self._session_data[session_id] = [env_id]  # environment index
        return (self._agent_tell_key_req, 2)

    def _agent_tell_key_req(self, session_id, chunk):
        """Return the expected evidence key length."""
        try:
            key_len = struct.unpack('>H', chunk)[0]
        except struct.error as ex:
            self.logger.warning(
                "Session id: %d, struct error when unpacking evidence key length: %s",
                session_id, ex)
            return None

        return (self._agent_tell_key_post, key_len)

    def _agent_tell_key_post(self, session_id, key):
        """Evidence key name given."""
        self._session_data[session_id].append(key)
        return (self._agent_tell_update, 4)

    def _agent_tell_update(self, session_id, chunk):
        """Update env evidence key with value given."""
        try:
            env_val = struct.unpack('>L', chunk)[0]
        except struct.error as ex:
            self.logger.warning(
                "Session id: %d, struct error when unpacking env evidence value: %s",
                session_id, ex)
            return None

        env_update = self._session_data[session_id]
        self._env_evidence[env_update[0]][env_update[1]] = env_val

        self.logger.debug(
            "Session id: %d, Successfully updated env id %d, state key '%s' with value %d.",
            session_id, env_update[0], env_update[1], env_val)

        # TODO: call appropriate update method to update environment based on evidence update

        return (self._agent_query, 6)

    # agent env id request
    def _agent_env_reg_req(self, session_id, context_len):
        """Remote agent wants the env id for a given env context."""
        return (self._agent_env_reg_post, context_len)

    def _agent_env_reg_post(self, session_id, env_context):
        """Environment context name to register."""
        if env_context not in self._env_map:
            self.logger.warning("Session id: %d, env context '%s' is not registered.",
                                session_id, env_context)
            return None

        return (self._env_map[env_context], (self._agent_query, 6))
