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
            service_config = cls._process_config(emews.base.config.parse(service_config_path))
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
            service_obj = service_class(service_config['config'], _inject=service_config['inject'])
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
        for index, modifier_dict in enumerate(service_config.get('modifiers', [])):
            # syntax validation
            if not isinstance(modifier_dict, collections.Mapping):
                cls.logger.error("Modifier for '%s' at index %d not a dictionary.",
                                 service_obj.__class__.__name__, index)
                raise TypeError("Modifier for '%s' at index %d not a dictionary." %
                                service_obj.__class__.__name__, index)
            if len(modifier_dict) > 1:
                cls.logger.error("Modifier for '%s' at index %d contains multiple entries.",
                                 service_obj.__class__.__name__, index)
                raise AttributeError("Modifier for '%s' at index %d contains multiple entries." %
                                     service_obj.__class__.__name__, index)

            modifier_name = modifier_dict.keys()[0]
            cls.logger.debug("Importing modifier '%s' for service '%s'.",
                             modifier_name, service_obj.__class__.__name__)
            modifier_config = cls._process_config(modifier_dict)
            modifier_config['inject'] = {}
            modifier_config['inject']['_recipient_service'] = prev_instantiation

            module_name, class_name = emews.base.import_tools.format_path_and_class(
                'emews.services.modifiers', modifier_name)

            try:
                current_instantiation = emews.base.import_tools.import_class(
                    module_name, class_name)
            except ImportError:
                cls.logger.error("Modifier module '%s' could not be imported.",
                                 modifier_name.lower())
                raise

            try:
                current_instantiation = current_instantiation(_inject=base_decorator_config)
            except AttributeError as ex:
                self.logger.error("Extension '%s' could not be instantiated: %s",
                                  decorator_name, ex)
                raise

            self.logger.debug("Extension '%s' applied to %s.", decorator_name, service_obj.__class__.__name__)
            prev_instantiation = current_instantiation

        return current_instantiation

    def _instantiate_dependencies(self, config):
        '''
        Instantiates (or at least imports the class) all dependency objects declared in the input
        config.
        '''
        dependency_instantiation_dict = dict()
        for dep_name, dependency in config.iteritems():
            self.logger.debug("Resolving helper '%s'.", dep_name)
            try:
                module_name, class_name = self._get_path_and_class(
                    'emews.helpers', dependency['helper'])
            except KeyError as ex:
                self.logger.error("Required key missing from configuration for helper '%s': %s",
                                  dep_name, ex)
                raise

            # check optional params
            b_instantiate = True
            if 'instantiate' in dependency:
                if not isinstance(dependency['instantiate'], bool):
                    self.logger.error("In helper '%s': Key 'instantiate' must have a "\
                                      "boolean value (given value: %s).",
                                      dep_name, dependency['instantiate'])
                    raise ValueError(
                        "Key 'instantiate' must have a boolean value (given value: %s)." %
                        str(dependency['instantiate']))
                else:
                    b_instantiate = dependency['instantiate']

            try:
                class_object = emews.base.importclass.import_class_from_module(
                    module_name, class_name)
            except ImportError as ex:
                self.logger.error("Could not import helper '%s': %s",
                                  dep_name, ex)
                raise

            # Currently dependencies are not allowed to have dependencies.
            if 'config' in dependency:
                dep_config = dependency['config']
                self.logger.debug("Found config information for helper '%s'.", dep_name)
            else:
                dep_config = {}
                self.logger.debug("No config information found for helper '%s'.", dep_name)

            emews.base.config.Config(dep_config)

            if b_instantiate:
                try:
                    dependency_instantiation_dict[dep_name] = class_object(
                        _inject={'config': dep_config})
                except AttributeError as ex:
                    self.logger.error("Helper '%s' could not be instantiated: %s", dep_name, ex)
                    raise
                self.logger.debug("Helper '%s' instantiated.", dep_name)
            else:
                # instantiation not requested
                # DelayedInstantiation is callable.  self.helpers.<dep_name>.instantiate() to
                # instantiate.
                dependency_instantiation_dict[dep_name] = \
                    {'instantiate': \
                        emews.base.config.DelayedInstantiation(class_object, dep_config)}
                self.logger.debug("Helper '%s' requested not to instantiate.", dep_name)

        return dependency_instantiation_dict

    @classmethod
    def _process_config(cls, config):
        '''
        Process the raw config dict to a ServiceConfig.
        '''
        base_service_config = dict()
        base_service_config['config'] = {} if config is None else config.get('config', {})
        if config is not None and 'helpers' in config:
            base_service_config['helpers'] = self._instantiate_dependencies(
                self.config['helpers'])
        else:
            base_service_config['helpers'] = {}

        return {'config': emews.base.config.Config(base_service_config)}
