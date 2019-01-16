"""
BaseObject: Convenience class that provides system properties as fields.

Enables consistency from derived classes by providing a common methodology of system property access
using self.

Created on Apr 9, 2018
@author: Brian Ricks
"""


class BaseObject(object):
    """classdocs."""

    # We deny the creation of the instance __dict__ by default to save memory, as it is expected
    # that many instances of certain child classes (samplers for example) will be created for a
    # single eMews daemon instance, and most eMews child classes inherit BaseObject (which in
    # itself means we need __slots__ defined here).
    # Any child classes in which a __dict__ is preferable can simply omit the __slots__ declaration
    # in its own class definition.
    __slots__ = ('sys', 'logger')

    # This is set during eMews system init, once the system properties are known, and BEFORE any
    # BaseObject instances are instantiated
    _SYSTEM_PROPERTIES = None

    def __init__(self):
        """Constructor"""
        self.sys = _SYSTEM_PROPERTIES
        self.logger = _SYSTEM_PROPERTIES.logger
