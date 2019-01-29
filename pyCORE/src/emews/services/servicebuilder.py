"""
Builder for services.  Handles things such as configuration and which service to actually build.

Created on Apr 2, 2018
@author: Brian Ricks
"""
import collections
import os

import emews.base.baseobject
import emews.base.config
import emews.base.import_tools


class ServiceBuilder(emews.base.baseobject.BaseObject):
    """classdocs."""

    def result(self):
        """Return a new service."""
        return self._build_service()

    @classmethod
    def build(cls, service_name, service_config_name=None):
        """Build the service."""
        # service config
        if service_config_name is None:
            service_config_name = service_name.lower() + ".yml"

        service_config_path = os.path.join(cls.sys.root_path, "services", service_config_name)

        try:
            service_config = emews.base.config.parse(service_config_path)
        except IOError:
            cls.logger.error("Could not load service configuration: %s", service_config_path)
            raise

        cls.logger.debug("Loaded service configuration: %s", service_config_path)

        # import service module
        try:
            service_class = emews.base.import_tools.import_service(service_name)
        except ImportError:
            cls.logger.error("Service module '%s' could not be imported.", service_name)
            raise

        # instantiate service object
        try:
            service_obj = service_class(service_config['parameters'],
                                        _inject=service_config['inject'])
            cls.logger.debug("Service class '%s' instantiated.", service_name)
        except StandardError:
            cls.logger.error("Service '%s' could not be instantiated.", service_name)
            raise

        # build service modifiers
        cls._build_modifiers(service_obj, service_config)

    @classmethod
    def _build_modifiers(cls, service_obj, service_config):
        """Build the service."""
        # TODO: remove all helper code
        # TODO: Add 'name' to base_service_config as a new key.  Name is the service class name + an
        # ID which is unique to the service class (ie, AutoSSH will have it's own IDs starting from
        # zero).
        prev_instantiation = service_obj  # starting instantiation is the service object
        # check config for modifiers, and if exists, add them in order
        for index, modifier_config in enumerate(service_config.get('modifiers', [])):
            # syntax validation
            if not isinstance(modifier_config, collections.Mapping):
                cls.logger.error("Modifier for '%s' at index %d not a dictionary.",
                                 service_obj.__class__.__name__, index)
                raise TypeError("Modifier for '%s' at index %d not a dictionary." %
                                service_obj.__class__.__name__, index)
            if len(modifier_config) > 1:
                cls.logger.error("Modifier for '%s' at index %d contains multiple entries.",
                                 service_obj.__class__.__name__, index)
                raise AttributeError("Modifier for '%s' at index %d contains multiple entries." %
                                     service_obj.__class__.__name__, index)

            modifier_name = modifier_config.keys()[0]
            cls.logger.debug("Importing modifier '%s' for service '%s'.",
                             modifier_name, service_obj.__class__.__name__)
            modifier_config['inject'] = {}
            modifier_config['inject']['_recipient_service'] = prev_instantiation

            module_name, class_name = emews.base.import_tools.format_path_and_class(
                'emews.services.modifiers', modifier_name)

            try:
                current_instantiation = emews.base.import_tools.import_class(
                    module_name, class_name)
            except ImportError:
                cls.logger.error("Modifier module '%s' for service '%s' could not be imported.",
                                 modifier_name.lower(), service_obj.__class__.__name__)
                raise

            try:
                current_instantiation = current_instantiation(modifier_config['parameters'],
                                                              _inject=modifier_config['inject'])
            except StandardError:
                cls.logger.error("Modifier '%s' for service '%s' could not be instantiated.",
                                 modifier_name, service_obj.__class__.__name__)
                raise

            cls.logger.debug("Modifier '%s' applied to service '%s'.",
                             modifier_name, service_obj.__class__.__name__)
            prev_instantiation = current_instantiation

        return current_instantiation
