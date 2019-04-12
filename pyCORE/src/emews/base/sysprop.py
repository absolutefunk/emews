"""
System Properties.

Created on Apr 4, 2019
@author: Brian Ricks
"""


class SysProp(object):
    """Provides a read-only container for the system properties."""

    MSG_RO = "System properties are read-only."

    # All system properties defined here
    __slots__ = ('logger',
                 'node_name',
                 'node_id',
                 'root_path',
                 'is_hub',
                 'local')

    def __init__(self, **kwargs):
        """Constructor."""
        for key, value in kwargs.iteritems():
            object.__setattr__(self, key, value)

    def __setattr__(self, attr, value):
        """Attributes are not mutable."""
        raise AttributeError(SysProp.MSG_RO)
