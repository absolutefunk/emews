"""
Base class for query-based networking servers.

Created on Apr 28, 2019
@author: Brian Ricks
"""
import emews.base.baseserv


class QueryServ(emews.base.baseserv.BaseServ):
    """Classdocs."""

    __slots__ = ('_net_cache', '_net_client', 'query_handler')

    def __init__(self):
        """Constructor."""
        super(QueryServ, self).__init__()
        self.query_handler = emews.base.baseserv.Handler(self._query, 'H')

    def handle_init(self, node_id, session_id):
        """Session init."""
        self.serv_init(node_id, session_id)
        return self.query_handler

    def handle_close(self, session_id):
        """Session termination."""
        self.serv_close(session_id)

    def _query(self, session_id, req_id):
        """Process a request sent by a node."""
        try:
            handler = self.handlers[req_id]
        except IndexError:
            self.logger.warning("Session id: %d, invalid query request id: %d", session_id, req_id)
            return None

        if not len(handler.recv_list):
            # handler doesn't need any data received
            return handler.callback(session_id)

        return handler
