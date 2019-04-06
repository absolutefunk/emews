"""
System Properties.

Created on Apr 4, 2019
@author: Brian Ricks
"""
import emews.base.import_tools


class SysProp(object):
    """Provides a read-only container for the system properties."""

    MSG_RO = "System properties are read-only."

    class NetProp(object):
        """Container for net properties."""

        __slots__ = ('get_hub_addr',
                     'get_addr_from_name',
                     'connect_node')

        def __init__(self, **kwargs):
            """Constructor."""
            for key, value in kwargs.iteritems():
                object.__setattr__(self, key, value)

        def __setattr__(self, attr, value):
            """Attributes are not mutable."""
            raise AttributeError(SysProp.MSG_RO)

    # All system properties defined here
    __slots__ = ('logger',
                 'node_name',
                 'node_id',
                 'root_path',
                 'is_hub',
                 'local',
                 'net')

    def __init__(self, **kwargs):
        """Constructor."""
        netprop = kwargs.pop('net')

        for key, value in kwargs.iteritems():
            object.__setattr__(self, key, value)

        self.net = emews.base.sysprop.SysProp.NetProp(netprop)

    def __setattr__(self, attr, value):
        """Attributes are not mutable."""
        raise AttributeError(SysProp.MSG_RO)

    # sysprop methods
    def import_component(self, config):
        """Given a config dict, return an instantiated component."""
        class_name = config['component'].split('.')[-1]
        module_path = 'emews.components.' + config['component'].lower()

        inject_dct = {}
        inject_dct['_sys'] = self
        inject_dct['logger'] = self.logger

        return emews.base.import_tools.import_class_from_module(
            module_path, class_name)(config['parameters'], _inject=inject_dct)
