"""
Base class for network handlers.

Created on Mar 15, 2019
@author: Brian Ricks
"""


class BaseHandler(object):
    """Classdocs."""

    __slots__ = ('_state')

    def __init__(self):
        """Constructor."""
        self._state = {}
