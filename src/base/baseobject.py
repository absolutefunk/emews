"""
Base class that contains common functionality.

Created on Apr 17, 2019
@author: Brian Ricks
"""
import emews.base.logger
import emews.base.meta


class BaseObject(object):
    """Classdocs."""

    __metaclass__ = emews.base.meta.InjectionMetaWithABC
    __slots__ = ('sys', 'logger', '_interrupted')

    def __init__(self):
        """Constructor."""
        self.logger = emews.base.logger.get_logger()
        self._interrupted = False

    def interrupt(self):
        """Set the self._interrupt flag."""
        self._interrupted = True
