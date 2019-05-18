"""
Agent server.

Handles agent communication on the hub.

Created on Apr 3, 2019
@author: Brian Ricks
"""
import emews.base.baseserv
import emews.base.enums
import emews.base.import_tools
import emews.base.queryserv


class ServAgent(emews.base.queryserv.QueryServ):
    """Classdocs."""

    __slots__ = ('_env_id', '_env_handler', '_thread_dispatcher')

    @classmethod
    def build_protocols(cls):
        """Build the protocols for this server, and add them to BaseServ.protocols."""
        proto_id = emews.base.enums.net_protocols.NET_AGENT
        cls.protocols[proto_id] = [None] * emews.base.enums.agent_protocols.ENUM_SIZE

        new_proto = emews.base.baseserv.NetProto(
            'Ls', type_return='s',
            proto_id=proto_id,
            request_id=emews.base.enums.agent_protocols.AGENT_ASK)
        cls.protocols[proto_id][new_proto.request_id] = new_proto

        new_proto = emews.base.baseserv.NetProto(
            'LsL', type_return='H',
            proto_id=proto_id,
            request_id=emews.base.enums.agent_protocols.AGENT_TELL)
        cls.protocols[proto_id][new_proto.request_id] = new_proto

        new_proto = emews.base.baseserv.NetProto(
            's', type_return='L',
            proto_id=proto_id,
            request_id=emews.base.enums.agent_protocols.AGENT_ENV_ID)
        cls.protocols[proto_id][new_proto.request_id] = new_proto

    def __init__(self, thread_dispatcher):
        """Constructor."""
        super(ServAgent, self).__init__()

        self._thread_dispatcher = thread_dispatcher

        self.handlers = [None] * emews.base.enums.agent_protocols.ENUM_SIZE
        proto_id = emews.base.enums.net_protocols.NET_AGENT

        request_id = emews.base.enums.agent_protocols.AGENT_ASK
        self.handlers[request_id] = emews.base.baseserv.Handler(self.protocols[proto_id][request_id], self._agent_ask_env_req)

        request_id = emews.base.enums.agent_protocols.AGENT_TELL
        self.handlers[request_id] = emews.base.baseserv.Handler(self.protocols[proto_id][request_id], self._agent_tell_env_req)

        request_id = emews.base.enums.agent_protocols.AGENT_ENV_ID
        self.handlers[request_id] = emews.base.baseserv.Handler(self.protocols[proto_id][request_id], self._agent_env_id_req)

        self._env_id = {}  # [env_service_name]: id
        self._env_handler = []  # agent environment callback assigned to env id at index
        self._env_handler.append(None)  # env id 0 is invalid

    def _env_register(self, service_name):
        """Register a new agent environment."""
        try:
            env_obj = emews.base.import_tools.import_class_from_module(
                "emews.services.%s.%s_env" % (service_name.lower(), service_name.lower()),
                class_name=service_name + 'Env')
        except ImportError:
            self.logger.error(
                "Agent environment class '%s' could not be imported.", service_name + 'Env')
            raise

        new_env_id = len(self._env_handler)
        self._env_id[service_name] = new_env_id
        self._env_handler.append(
            [service_name,
             env_obj(_inject={
                'sys': self.sys,
                'env_name': service_name + 'Env',
                '_env_id': new_env_id,
                '_thread_dispatcher': self._thread_dispatcher
                })])

        self.logger.info("Agent environment '%s_env' assigned id: %d.", service_name)

        return new_env_id

    def serv_init(self, node_id, session_id):
        """Init of new agent session."""
        pass

    def serv_close(self, session_id):
        """Close a session."""
        pass

    # agent ask
    def _agent_ask_env_req(self, session_id, env_id):
        """
        Remote agent wants the available evidence from the given env_id.

        As evidence is variable in size, we return it as a string.
        """
        if env_id < 1 or env_id >= len(self._env_handler):
            self.logger.warning("Session id: %d, env id '%d' not registered.", session_id, env_id)
            return ('0', self.query_handler)  # '0' should be treated as invalid

        ev_str = self._env_handler[env_id][1].get_evidence()

        return (ev_str, self.query_handler)

    # agent tell
    def _agent_tell_env_req(self, session_id, env_id, obs_key, obs_val):
        """Agent is going to update an observation key's value corresponding to the given env id."""
        if env_id < 1 or env_id >= len(self._env_handler):
            self.logger.warning("Session id: %d, env id '%d' not registered.", session_id, env_id)
            return (emews.base.enums.net_state.STATE_NACK, self.query_handler)

        self._env_handler[env_id][1].put_observation(
            obs_key, self._net_cache.session.node_id, obs_val)

        return (emews.base.enums.net_state.STATE_ACK, self.query_handler)

    # agent env id request
    def _agent_env_id_req(self, session_id, service_name):
        """Remote agent wants the env id for its environment."""
        if service_name not in self._env_id:
            # register the service environment
            return (self._env_register(service_name), self.query_handle)

        return (self._env_id[service_name], self.query_handler)
