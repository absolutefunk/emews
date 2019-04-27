"""
Service spawner server.

Created on Apr 19, 2019
@author: Brian Ricks
"""
import struct

import emews.base.baseserv
import emews.base.enums
import emews.services.servicebuilder


class ServSpawner(emews.base.baseserv.BaseServ):
    """Classdocs."""

    __slots__ = ('_cb', '_session_data', '_thread_dispatcher')

    def __init__(self, thread_dispatcher):
        """Constructor."""
        super(ServSpawner, self).__init__()

        self._thread_dispatcher = thread_dispatcher

        self._cb = [None] * emews.base.enums.spawner_protocols.ENUM_SIZE
        self._cb[emews.base.enums.spawner_protocols.SPAWNER_LAUNCH_SERVICE] = \
            self._spawn_service_req_name

        self._session_data = {}

    def serv_init(self, node_id, session_id):
        """Init of new session.  Next expected chunk is request from node."""
        self._session_data[session_id] = None
        return (self._spawn_query, 6)

    def serv_close(self, session_id):
        """Close a session."""
        del self._session_data[session_id]

    def _spawn_query(self, session_id, chunk):
        """
        Process a request sent by a node.

        req_id (2 bytes) + param_s (4 bytes)
        """
        try:
            req_id, param_s = struct.unpack('>HL', chunk)
        except struct.error as ex:
            self.logger.warning("Session id: %d, struct error when unpacking spawner query: %s",
                                session_id, ex)
            return None

        try:
            ret_tup = self._cb[req_id](session_id, param_s)
        except IndexError:
            self.logger.warning("Session id: %d, invalid query id: %d", session_id, req_id)

        self.logger.debug("Session id: %d, received request id: %d", session_id, req_id)

        return ret_tup

    def _spawn_service_req_name(self, session_id, str_length):
        """Request to spawn a service.  str_length is expected length of service name."""
        self._session_data[session_id] = str_length  # cache this for next cb
        return (self._spawn_service_post_name, str_length)

    def _spawn_service_post_name(self, session_id, chunk):
        """Service name given."""
        self._session_data[session_id] = chunk  # cache this for next cb

        return (self._spawn_service_req_config, 4)

    def _spawn_service_req_config(self, session_id, chunk):
        """Length of string of service config name."""
        try:
            str_length = struct.unpack('>L', chunk)[0]
        except struct.error as ex:
            self.logger.warning(
                "Session id: %d, struct error when unpacking service config name length: %s",
                session_id, ex)
            return None

        if str_length > 0:
            return (self._spawn_service_post, str_length)

        self.logger.debug(
            "Session id: %d, service config path length is zero, will resolve default path ...",
            session_id)
        return self._spawn_service_post(session_id, None)

    def _spawn_service_post(self, session_id, chunk):
        """Given the service class and config name, spawn the service."""
        service_name = self._session_data[session_id]
        service_config_name = chunk

        service_builder = emews.services.servicebuilder.ServiceBuilder(_inject={'sys': self.sys})

        try:
            service_obj = service_builder.build(
                service_name, service_config_file=service_config_name)
        except StandardError as ex:
            self.logger.warning(
                "Session id: %d, ServiceBuilder threw exception while building service: %s: %s",
                session_id, ex.__class__.__name__, ex)
            return (struct.pack('>H', emews.base.enums.net_state.STATE_NACK), (None,))

        self._thread_dispatcher.dispatch(service_obj)
        return (struct.pack('>H', emews.base.enums.net_state.STATE_ACK), (None,))
