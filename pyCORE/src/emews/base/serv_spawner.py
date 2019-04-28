"""
Service spawner server.

Created on Apr 19, 2019
@author: Brian Ricks
"""
import emews.base.baseserv
import emews.base.enums
import emews.base.queryserv
import emews.services.servicebuilder


class ServSpawner(emews.base.queryserv.QueryServ):
    """Classdocs."""

    __slots__ = ('_thread_dispatcher')

    def __init__(self, thread_dispatcher):
        """Constructor."""
        super(ServSpawner, self).__init__()

        self._thread_dispatcher = thread_dispatcher

        self.handlers = [None] * emews.base.enums.spawner_protocols.ENUM_SIZE
        self.handlers[emews.base.enums.spawner_protocols.SPAWNER_LAUNCH_SERVICE] = \
            emews.base.baseserv.Handler(self._spawn_service_req, 'ss', send_type_str='H')

    def serv_init(self, node_id, session_id):
        """Init of new session."""
        pass

    def serv_close(self, session_id):
        """Close a session."""
        pass

    def _spawn_service_req(self, session_id, service_name, service_config_name):
        """Request to spawn a service.  str_length is expected length of service name."""
        service_builder = emews.services.servicebuilder.ServiceBuilder(
            _inject={'sys': self.sys, '_net_client': self._net_client})

        try:
            service_obj = service_builder.build(
                service_name, service_config_file=service_config_name)
        except StandardError as ex:
            self.logger.warning(
                "Session id: %d, ServiceBuilder threw exception while building service: %s: %s",
                session_id, ex.__class__.__name__, ex)
            return (emews.base.enums.net_state.STATE_NACK, None)

        self._thread_dispatcher.dispatch(service_obj)
        return (emews.base.enums.net_state.STATE_ACK, None)
