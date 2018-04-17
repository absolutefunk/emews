'''
Builder for services.  Handles things such as configuration and which service to actually build.

Created on Apr 2, 2018
@author: Brian Ricks
'''
import emews.base.baseobject
import emews.base.config
from emews.base.configcomponent import ConfigComponent
import emews.base.importclass

class ServiceBuilder(emews.base.baseobject.BaseObject):
    '''
    classdocs
    '''
    def __init__(self, sys_config):
        '''
        Constructor
        '''
        super(ServiceBuilder, self).__init__(sys_config)

        self._is_interrupted = False
        self._config_component = None
        self._service_config = None
        self._service_class = None

    @property
    def result(self):
        '''
        return a new service
        '''
        return self.__build_service()

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
        module_path = self.config.get_sys('paths', 'emews_pkg_services_path')
        #because services are in a subfolder that is the same as their name, concatenate the module
        # name to the module_path.  Also, as we are passing the module name as part of the path,
        # concatenate the module name again.
        module_path += "." + module_name
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
        if val_config_path is None:
            return

        config_try_again = False
        try:
            config_dict = emews.base.config.parse(emews.base.config.prepend_path(val_config_path))
        except IOError as ex:
            # config file only may be given, try to prepend path to same folder as service module
            self.logger.warning("Service configuration could not be loaded, trying service path...")
            self.logger.debug(ex)
            config_try_again = True

        if config_try_again:
            try:
                config_dict = emews.base.config.parse(emews.base.config.prepend_path(
                    "../services/" + self._service_class.__name__.lower() + "/" + val_config_path))
            except IOError as ex:
                self.logger.error("Service configuration '%s' could not be loaded.",
                                  val_config_path)
                self.logger.debug(ex)
                raise
        self.logger.info("Service configuration '%s' loaded.", val_config_path)
        self._config_component = ConfigComponent(config_dict)

    def __build_service(self):
        '''
        builds the service
        '''
        if self._config_component is not None:
            service_config = self.config.clone_with_config(self._config_component)
        else:
            service_config = self.config

        try:
            service_instantiation = self._service_class(service_config)
        except StandardError as ex:
            self.logger.error("Service class could not be instantiated.")
            self.logger.debug(ex)
            raise

        self.logger.debug("Service class '%s' instantiated.",
                          service_instantiation.__class__.__name__)
        current_instantiation = service_instantiation
        # Check config for decorators, and add any found.  Note, the structure in the config in
        # regards to decorators needs to follow a specific ordering:
        # ['decorators'] --> [<DecoratorClass>] --> (config dict/list/etc for DecoratorClass)
        # If no config_path for the service was given, then this section is skipped.
        if 'decorators' in service_config.component_config:
            decorator_class_path = self.config.get_sys(
                'paths', 'emews_pkg_service_decorators_path')
            self.logger.debug("Decorator module path: %s", decorator_class_path)
            for decorator_name, _ in service_config.get('decorators').iteritems():
                if self._is_interrupted:
                    return None

                self.logger.debug("Resolving decorator '%s' for %s.",
                                  decorator_name, service_instantiation.__class__.__name__)
                try:
                    current_instantiation = emews.base.importclass.import_class(
                        decorator_name, decorator_class_path)(current_instantiation)
                except KeyError as ex:
                    self.logger.error("(A key is missing from the config): %s", ex)
                    raise
                except ImportError as ex:
                    self.logger.error("Module '%s' could not be resolved into a module: %s",
                                      decorator_name.lower(), ex)
                    raise
                except AttributeError as ex:
                    self.logger.error("Decorator '%s' could not be resolved into a class.",
                                      decorator_name)
                    self.logger.debug(ex)
                    raise
                self.logger.debug("Decorator '%s' applied to %s.",
                                  decorator_name, service_instantiation.__class__.__name__)

        return current_instantiation
