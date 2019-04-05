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

    class HandlerAgent(emews.base.basehandler.BaseClientHandler):
        """Handler for networking tasks.""""

        __slots__ = ()

        def handle_init(self, id):
            """Connection established, prepare to write."""
            pass

        def handle_write(self, id):
            """Handle writable socket."""
            pass

        def handle_close(self, id):
            """Handle connection close."""
            pass

    def __init__(self):
        """Constructor."""
        super(BaseAgent, self).__init__()
        self._net_handler = HandlerAgent(_inject={
            '_sys': self._sys,
            'logger': self._sys.logger
        })


    def sense(self, context):
        """
        Sense the environment, returning an environment state.

        Environmental 'sensing' is accomplished by asking eMews what the environment looks like
        given some context, such as a webpage and other state.
        """
        return None
