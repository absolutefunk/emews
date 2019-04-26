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

    __slots__ = ('node_name',
                 'node_id',
                 'root_path',
                 'is_hub',
                 'local')

    def __init__(self, **kwargs):
        """Constructor."""
        for attr, value in kwargs.iteritems():
            object.__setattr__(attr, value)

    def __setattr__(self, attr, value):
        """Attributes are not mutable."""
        raise AttributeError(SysProp.MSG_RO)

    # SysProp service methods
    # TODO: move this somewhere else
    def import_component(self, config):
        """Import a component from a properly formatted config dictionary."""
        class_name = config['component'].split('.')[-1]
        module_path = 'emews.components.' + config['component'].lower()

        inject_dict = {'logger': emews.base.logger.get_logger(), '_sys': self}

        return emews.base.import_tools.import_class_from_module(
            module_path, class_name)(config['parameters'], _inject=inject_dict)
