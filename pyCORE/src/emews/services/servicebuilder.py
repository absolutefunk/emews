"""
Builder for services.  Handles things such as configuration and which service to actually build.

Created on Apr 2, 2018
@author: Brian Ricks
"""
import collections
import os

import emews.base.config
import emews.base.import_tools


class ServiceBuilder(object):
    """classdocs."""

    __slots__ = ('_sys')

    def __init__(self, sysprop):
        """Constructor."""
        self._sys = sysprop

    def build(self, service_name, service_config_dict=None, service_config_file=None):
        """Build the service."""
        if service_config_dict is not None:
            service_config = service_config_dict
            self._sys.logger.debug("Using service configuration passed as argument.")
        else:
            if service_config_file is None:
                service_config_file = service_name.lower() + ".yml"

            service_config_path = os.path.join(
                self._sys.root_path, "services", service_name.lower(), service_config_file)

            try:
                service_config = emews.base.config.parse(service_config_path)
            except IOError:
                self._sys.logger.error("Could not load service configuration: %s",
                                       service_config_path)
                raise

            self._sys.logger.debug("Loaded service configuration: %s", service_config_path)

        # import service module
        try:
            service_class = emews.base.import_tools.import_service(service_name)
        except ImportError:
            self._sys.logger.error("Service module '%s' could not be imported.", service_name)
            raise

        # TODO: Add global service identifiers (will need to have a central server for this)

        # inject dict
        service_config_inject = {}
        service_config_inject['service_name'] = service_name
        service_config_inject['service_id'] = -1  # TODO: set this to the actual service id (global)
        service_config_inject['_sys'] = self._sys
        service_config_inject['logger'] = self._sys.logger

        # instantiate service object
        try:
            service_obj = service_class(service_config['parameters'],
                                        _inject=service_config_inject)
            self._sys.logger.debug("Service class '%s' instantiated.", service_name)
        except StandardError:
            self._sys.logger.error("Service '%s' could not be instantiated.", service_name)
            raise

        # build service modifiers
        return self._build_modifiers(service_obj, service_config)

    @classmethod
    def _build_modifiers(self, service_obj, service_config):
        """Build the service."""
        current_instantiation = service_obj  # starting instantiation is the service object
        # check config for modifiers, and if exists, add them in order
        for index, modifier_config in enumerate(service_config.get('modifiers', [])):
            # syntax validation
            if not isinstance(modifier_config, collections.Mapping):
                self._sys.logger.error("Modifier for '%s' at index %d not a dictionary.",
                                       service_obj.__class__.__name__, index)
                raise TypeError("Modifier for '%s' at index %d not a dictionary." %
                                service_obj.__class__.__name__, index)
            if len(modifier_config) > 1:
                self._sys.logger.error("Modifier for '%s' at index %d contains multiple entries.",
                                       service_obj.__class__.__name__, index)
                raise AttributeError("Modifier for '%s' at index %d contains multiple entries." %
                                     service_obj.__class__.__name__, index)

            modifier_name = modifier_config.keys()[0]
            self._sys.logger.debug("Importing modifier '%s' for service '%s'.",
                                   modifier_name, service_obj.__class__.__name__)

            module_name, class_name = emews.base.import_tools.format_path_and_class(
                'emews.services.modifiers', modifier_name)

            modifier_config = modifier_config[modifier_name]
            prev_instantiation = current_instantiation

            try:
                current_instantiation = emews.base.import_tools.import_class_from_module(
                    module_name, class_name)
            except ImportError:
                self._sys.logger.error(
                    "Modifier module '%s' for service '%s' could not be imported.",
                    modifier_name.lower(), service_obj.__class__.__name__)
                raise

            modifier_config_inject = {}
            modifier_config_inject['_recipient_service'] = prev_instantiation

            try:
                current_instantiation = current_instantiation(
                    modifier_config['parameters'], _inject=modifier_config_inject) \
                    if isinstance(modifier_config, collections.Mapping) and \
                    'parameters' in modifier_config else current_instantiation(
                        _inject=modifier_config_inject)
            except StandardError:
                self._sys.logger.error("Modifier '%s' for service '%s' could not be instantiated.",
                                       modifier_name, service_obj.__class__.__name__)
                raise

            self._sys.logger.debug("Modifier '%s' applied to service '%s'.",
                                   modifier_name, service_obj.__class__.__name__)

        return current_instantiation
