"""
System Properties.

Created on Apr 4, 2019
@author: Brian Ricks
"""
import emews.base.import_tools


class SysProp(object):
    """Provides a read-only container for the system properties."""

    class NetProp(object):
        """Container for net properties."""

        __slots__ = ('get_hub_addr',
                     'get_addr_from_name',
                     'connect_node')

        def __init__(self):
            """Constructor."""
            self.get_hub_addr = None  # to be redefined when method is available
            self.get_addr_from_name = None
            self.connect_node = None

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
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        self.net = emews.base.sysprop.SysProp.NetProp()

    def import_component(self, config):
        """Given a config dict, return an instantiated component."""
        class_name = config['component'].split('.')[-1]
        module_path = 'emews.components.' + config['component'].lower()

        inject_dct = {}
        inject_dct['_sys'] = self
        inject_dct['logger'] = self._logger

        return emews.base.import_tools.import_class_from_module(
            module_path, class_name)(config['parameters'], _inject=inject_dct)
