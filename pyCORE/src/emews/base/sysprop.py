"""
System Properties.

Created on Apr 4, 2019
@author: Brian Ricks
"""


def unassigned_method(*params):
    """Unassigned sysprop method."""
    raise NotImplementedError("Sysprop method unassigned.")


class SysProp(object):
    """Provides a read-only container for the system properties."""

    MSG_RO = "System properties are read-only."

    class NetProp(object):
        """Provides a read-only container for the system net properties."""

        # Net system properties
        __slots__ = ('_ro'
                     'hub_query')

        def __init__(self, **kwargs):
            """Constructor."""
            self._ro = False
            self.hub_query = unassigned_method

        def __setattr__(self, attr, value):
            """Attributes are not mutable."""
            if self._ro:
                raise AttributeError(SysProp.MSG_RO)

            object.__setattr__(self, attr, value)

    # Root system properties
    __slots__ = ('_ro'
                 'node_name',
                 'node_id',
                 'root_path',
                 'is_hub',
                 'local',
                 'net')

    def __init__(self, **kwargs):
        """Constructor."""
        self._ro = False
        self.net = SysProp.NetProp(kwargs.pop('net'))
        for attr, value in kwargs.iteritems():
            object.__setattr__(self, attr, value)

        def __setattr__(self, attr, value):
            """Attributes are not mutable."""
            if self._ro:
                raise AttributeError(SysProp.MSG_RO)

            object.__setattr__(self, attr, value)
