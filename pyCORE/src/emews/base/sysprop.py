"""
System Properties.

Created on Apr 4, 2019
@author: Brian Ricks
"""
import emews.base.logger
import emews.base.import_tools


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

        # SysProp service methods
        def import_component(config):
            """Import a component from a properly formatted config dictionary."""
            class_name = config['component'].split('.')[-1]
            module_path = 'emews.components.' + config['component'].lower()

            inject_dict = {'logger': emews.base.logger.get_logger(), '_sys': self}

            return emews.base.import_tools.import_class_from_module(
                module_path, class_name)(config['parameters'], _inject=inject_dict)
