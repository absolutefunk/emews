"""
Base class for networking servers.

Created on Apr 2, 2019
@author: Brian Ricks
"""
import emews.base.meta


class BaseServ:
    """Classdocs."""

    __metaclass__ = emews.base.meta.InjectionMetaWithABC
    __slots__ = ("_sys", "logger")

    @property
    def sys(self):
        """Return the system properties object."""
        return self._sys
