'''
Builder for services.  Handles things such as configuration and which service to actually build.

Created on Apr 2, 2018
@author: Brian Ricks
'''
import os

import emews.base.baseobject
import emews.base.config
import emews.base.importclass

class ServiceBuilder(emews.base.baseobject.BaseObject):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        super(ServiceBuilder, self).__init__()

        self._is_interrupted = False
        self._service_config = None
        self._service_class = None

    @property
    def result(self):
        '''
        return a new service
        '''
        return self._build_service()

    def stop(self):
        '''
        Sets a stop flag.  Only useful if builder is instantiating decorators in a loop.
        '''
        self.logger.debug("Stop flag set.")
        self._is_interrupted = True

    def service(self, val_service_name):
        '''
        Sets the service.  We do parsing of the service name to the module and class here so they
        will be cached on build calls.
        '''
        # Attempt to resolve the module.  If using emews naming, then service should also resolve.
        module_name = val_service_name.lower()
        #because services are in a subfolder that is the same as their name, concatenate the module
        # name to the module_path.  Also, as we are passing the module name as part of the path,
        # concatenate the module name again.
        module_path = "emews.services." + module_name
        try:
            self._service_class = emews.base.importclass.import_class(val_service_name, module_path)
        except ImportError as ex:
            self.logger.error("Module name '%s' could not be resolved into a module: %s",
                              module_name, ex)
            raise
        except AttributeError as ex:
            self.logger.error("Service name '%s' could not be resolved into a class.",
                              val_service_name)
            self.logger.debug(ex)
            raise

    def config_path(self, val_config_path):
        '''
        Sets the configuration component for the service.  Parsing of the config path is done
        now for caching.
        '''
        self._service_config = None
        if val_config_path is None and self._service_class is not None:
            # attempt to resolve config file from default service config path and service class
            service_config_path = os.path.join(self.config.root_path, "services",
                                               self._service_class.__name__.lower(),
                                               self._service_class.__name__.lower() + ".yml")
            self.logger.info("No configuration file given, attempting to load default: %s",
                             service_config_path)
            try:
                config_dict = emews.base.config.parse(service_config_path)
            except IOError as ex:
                self.logger.warning("Could not load default configuration, continuing with none.")
                return
            self.logger.info("Loaded default configuration: %s", service_config_path)
            self._service_config = config_dict
            return

        config_try_again = False
        try:
            config_dict = emews.base.config.parse(val_config_path)
        except IOError:
            # config file only may be given, try to prepend path to same folder as service module
            self.logger.info("Service configuration could not be loaded, trying service path ...")
            config_try_again = True

        if config_try_again:
            try:
                config_dict = emews.base.config.parse(os.path.join(
                    self.config.root_path, "services", self._service_class.__name__.lower(),
                    val_config_path))
            except IOError as ex:
                self.logger.error("Service configuration '%s' could not be loaded.",
                                  val_config_path)
                self.logger.debug(ex)
                raise

        self.logger.info("Service configuration '%s' loaded.", val_config_path)
        self._service_config = config_dict

    def _build_service(self):
        '''
        builds the service
        '''
        #TODO: remove all helper code
        #TODO: Add 'name' to base_service_config as a new key.  Name is the service class name + an
        # ID which is unique to the service class (ie, AutoSSH will have it's own IDs starting from
        # zero).
        base_service_config = self._process_config(self._service_config)
        try:
            service_instantiation = self._service_class(_inject=base_service_config)
        except StandardError:
            self.logger.error("[%s] Service class could not be instantiated.",
                              self._service_class.__name__)
            raise

        service_name = service_instantiation.__class__.__name__
        self.logger.debug("Service class '%s' instantiated.",
                          service_name)
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

    def _process_config(self, config):
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
