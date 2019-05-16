"""
Agent server.

Handles agent communication on the hub.

Created on Apr 3, 2019
@author: Brian Ricks
"""
import emews.base.enums
import emews.base.baseserv
import emews.base.queryserv


class ServAgent(emews.base.queryserv.QueryServ):
    """Classdocs."""

    __slots__ = ('_env_evidence', '_env_state', '_env_id', '_env_id_map')

    def __init__(self):
        """Constructor."""
        super(ServAgent, self).__init__()
        self._net_client.protocols[emews.base.enums.net_protocols.NET_AGENT] = \
            [None] * emews.base.enums.agent_protocols.ENUM_SIZE

        self.handlers = [None] * emews.base.enums.agent_protocols.ENUM_SIZE

        new_proto = emews.base.baseserv.NetProto(
            'Ls', type_return='L',
            proto_id=emews.base.enums.net_protocols.NET_AGENT,
            request_id=emews.base.enums.agent_protocols.AGENT_ASK)
        self._net_client.protocols[new_proto.proto_id][new_proto.request_id] = new_proto
        self.handlers[new_proto.request_id] = emews.base.baseserv.Handler(new_proto, self._agent_ask_env_req)

        new_proto = emews.base.baseserv.NetProto(
            'LsL', type_return='H',
            proto_id=emews.base.enums.net_protocols.NET_AGENT,
            request_id=emews.base.enums.agent_protocols.AGENT_TELL)
        self._net_client.protocols[new_proto.proto_id][new_proto.request_id] = new_proto
        self.handlers[new_proto.request_id] = emews.base.baseserv.Handler(new_proto, self._agent_tell_env_req)

        new_proto = emews.base.baseserv.NetProto(
            's', type_return='L',
            proto_id=emews.base.enums.net_protocols.NET_AGENT,
            request_id=emews.base.enums.agent_protocols.AGENT_ENV_ID)
        self._net_client.protocols[new_proto.proto_id][new_proto.request_id] = new_proto
        self.handlers[new_proto.request_id] = emews.base.baseserv.Handler(new_proto, self._agent_env_id_req)

        self._env_evidence = []  # environment evidence cache
        self._env_state = []  # environment state cache
        self._env_evidence.append(None)  # env id 0 is invalid
        self._env_state.append(None)  # env id 0 is invalid
        self._env_id = 1

        self._env_id_map = {}  # env context to id mapping

    def env_register(self, from_env, env_context):
        """Register a new env context from an agent environment."""
        self._env_id_map[env_context] = self._env_id
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
            return (0, None)  # Note: passing back zero here may conflict with legit zero values

        state_val = self._env_state[env_id].get(state_key, None)

        if state_val is None:
            self.logger.warning("Session id: %d, env id: %d, state key '%s' does not exist.",
                                session_id, env_id, state_key)
            return (0, None)  # Note: passing back zero here may conflict with legit zero values

        return (state_val, self.query_handler)

    # agent tell
    def _agent_tell_env_req(self, session_id, env_id, ev_key, ev_val):
        """Agent is going to update an evidence key's value corresponding to the given env id."""
        if env_id < 1 or env_id >= len(self._env_evidence):
            self.logger.warning("Session id: %d, env id '%d' not registered.",
                                session_id, env_id)
            return (emews.base.enums.net_state.STATE_NACK, self.query_handler)

        self._env_evidence[env_id][ev_key] = ev_val

        self.logger.debug(
            "Session id: %d, Successfully updated env id %d, evidence key '%s' with value %d.",
            session_id, env_id, ev_key, ev_val)

        # TODO: call appropriate update method to update environment based on evidence update

        return (emews.base.enums.net_state.STATE_ACK, self.query_handler)

    # agent env id request
    def _agent_env_id_req(self, session_id, env_context):
        """Remote agent wants the env id for a given env context."""
        if env_context not in self._env_id_map:
            self.logger.warning("Session id: %d, env context '%s' is not registered.",
                                session_id, env_context)
            return (0, None)

        return (self._env_id_map[env_context], self.query_handler)
