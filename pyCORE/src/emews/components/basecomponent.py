"""
Class base for components.

Created on Feb 8, 2019
@author: Brian Ricks
"""
import emews.base.meta


class BaseComponent(object):
    """Classdocs."""

    __metaclass__ = emews.base.meta.InjectionMetaWithABC
    __slots__ = ('logger', '_sys')

    @property
    def sys(self):
        """Return the system properties object."""
        return self._sys
