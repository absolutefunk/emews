"""
Builder for services.  Handles things such as configuration and which service to actually build.

Created on Apr 2, 2018
@author: Brian Ricks
"""
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
            cls.logger.error("Service '%s' module could not be imported.", service_name)
            raise

        # instantiate service object
        try:
            service_obj = service_class(service_config['config'], _inject=service_config['inject'])
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


        service_name = service_instantiation.__class__.__name__
        cls.logger.debug("Service class '%s' instantiated.", service_name)
        prev_instantiation = service_instantiation
        # Check config for decorators (extensions), and add any found.
        if self._service_config is not None and 'extensions' in self._service_config:
            for decorator_name, decorator_config in self._service_config['extensions'].iteritems():
                if self._is_interrupted:
                    return None

                self.logger.debug("Resolving extension '%s' for %s.", decorator_name, service_name)
                base_decorator_config = self._process_config(decorator_config)
                # recipient_service is an extra attribute to define on extension construction
                base_decorator_config['extra'] = {}
                base_decorator_config['extra']['_di_recipient_service'] = prev_instantiation

                module_name, class_name = self._get_path_and_class(
                    'emews.services.extensions', decorator_name)

                try:
                    current_instantiation = emews.base.importclass.import_class(
                        module_name, class_name)
                except ImportError as ex:
                    self.logger.error("Module '%s' could not be resolved into a module: %s",
                                      decorator_name.lower(), ex)
                    raise
                except AttributeError as ex:
                    self.logger.error("Extension '%s' could not be resolved into a class: %s",
                                      decorator_name, ex)
                    raise

                try:
                    current_instantiation = current_instantiation(_inject=base_decorator_config)
                except AttributeError as ex:
                    self.logger.error("Extension '%s' could not be instantiated: %s",
                                      decorator_name, ex)
                    raise

                self.logger.debug("Extension '%s' applied to %s.", decorator_name, service_name)
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

    def _get_path_and_class(self, module_prefix, name):
        '''
        Formats the full module path and class name.
        '''
        type_and_class = name.split('.')
        module_path = module_prefix + '.' + \
                      '.'.join(type_and_class[:-1]) + \
                      '.' + type_and_class[-1].lower()
        class_name = type_and_class[-1]

        return zip(module_path, class_name)
