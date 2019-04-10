"""
Module for eMews services which act as agents.

Agent services interact with their environment, using eMews as an oracle.

Created on Mar 28, 2019
@author: Brian Ricks
"""
import emews.base.basehandler
import emews.services.baseservice


class BaseAgent(emews.services.baseservice.BaseService):
    """Classdocs."""

    __slots__ = ('_net_handler')

    class HandlerAgent(emews.base.basehandler.BaseHandler):
        """Handler for networking tasks."""

        __slots__ = ()

        def handle_init(self, id):
            """Post connection established, prepare to write."""
            return (self._send_query, 0)  # zero buf designates write mode

        def handle_close(self, id):
            """Handle connection close."""
            pass

        def _send_query(self, id):
            """Send the query."""
            return ("", self._recv_response, 8)  # TODO: put in actual query and expected bytes of response

        def _recv_response(self, id, chunk):
            """Response received from query."""

    def __init__(self):
        """Constructor."""
        super(BaseAgent, self).__init__()
        self._net_handler = emews.services.baseagent.BaseAgent.HandlerAgent(_inject={
            '_sys': self._sys,
            'logger': self._sys.logger
        })

    def ask(self, context):
        """
        Ask (sense) the environment, returning an environment state.

        Environmental 'sensing' is accomplished by asking eMews what the environment looks like
        given some context, such as a webpage and other state.
        """
        return None
