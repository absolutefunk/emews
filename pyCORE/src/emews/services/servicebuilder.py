'''
Builder for services.  Handles things such as configuration and which service to actually build.

Created on Apr 2, 2018

@author: Brian Ricks
'''
import ConfigParser
import importlib

import emews.base.config
from emews.base.configcomponent import ConfigComponent

class ServiceBuilder(object):
    '''
    classdocs
    '''
    def __init__(self, sys_config):
        '''
        Constructor
        '''
        self._sys_config = sys_config
        self._logger = self._sys_config.logger

        self._config_component = None
        self._service_config = None
        self._service_class = None

    @property
    def result(self):
        '''
        return a new service
        '''
        return self.__build_service()

    @property
    def logger(self):
        '''
        returns the logger object
        '''
        return self._logger

    @property
    def config(self):
        '''
        returns the system configuration object
        '''
        return self._sys_config

    @service.setter
    def service(self, val_service_name):
        '''
        Sets the service.  We do parsing of the service name to the module and class here so they
        will be cached on build calls.
        '''
        # Attempt to resolve the module.  If using emews naming, then service should also resolve.
        try:
            service_module = importlib.import_module(
                val_service_name.lowercase(), self.config.get_sys(
                    'paths', 'emews_pkg_services_path'))
        except ImportError as ex:
            self.logger.error("Service name could not be resolved into a module.")
            self.logger.debug(ex)
            raise

        try:
            self._service_class = getattr(service_module, val_service_name)
        except AttributeError as ex:
            self.logger.error("Service name could not be resolved into a class.")
            self.logger.debug(ex)
            raise

    @config.setter
    def config_path(self, val_config_path):
        '''
        Sets the configuration component for the service.  Parsing of the config path is done
        now for caching.
        '''
        if val_config_path is None:
            return

        try:
            config_dict = emews.base.config.parse(emews.config.prepend_path(val_config_path))
        except ConfigParser.Error as ex:
            self.logger.error("Service configuration could not be parsed.")
            self.logger.debug(ex)
            raise

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

        current_instantiation = service_instantiation
        # Check config for decorators, and add any found.  Note, the structure in the config in
        # regards to decorators needs to follow a specific ordering:
        # ['decorators'] --> [<DecoratorClass>] --> (config dict/list/etc for DecoratorClass)
        # If no config_path for the service was given, then this section is skipped.
        if 'decorators' in service_config.component_config:
            for service_decorator in service_config.get('decorators'):
                try:
                    service_decorator_class = service_instantiation.importclass(
                        service_decorator, self.config.get_sys(
                            'paths', 'emews_pkg_service_decorators_path'))
                except KeyError as ex:
                    self.logger.error("(A key is missing from the config): %s", ex)
                    raise

                current_instantiation = service_decorator_class(current_instantiation)

        return current_instantiation
