'''
Builder for services.  Handles things such as configuration and which service to actually build.

Created on Apr 2, 2018

@author: Brian Ricks
'''
import ConfigParser
import importlib

import emews.base.config

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

        self._config = None
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

    @service.setter
    def service(self, val_service_name):
        '''
        Sets the service.  We do parsing of the service name to the module and class here so they
        will be cached on build calls.
        '''
        # Attempt to resolve the module.  If using emews naming, then service should also resolve.
        try:
            service_module = importlib.import_module(
                val_service_name.lowercase(), self._sys_config.get_sys(
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
    def config(self, val_config_path):
        '''
        Sets the configuration.  We do parsing of the configuration here for caching, but do not
        add this configuration data to the system configuration until service creation.
        '''
        try:
            self._config = emews.config.parse(emews.config.prepend_path(val_config_path))
        except ConfigParser.Error as ex:
            self.logger.error("Service configuration could not be parsed.")
            self.logger.debug(ex)
            raise

    def __build_service(self):
        '''
        builds the service
        '''
        try:
            service_instantiation = self._service_class(self._sys_config)
        except StandardError as ex:
            self.logger.error("Service class could not be instantiated.")
            self.logger.debug(ex)
            raise

        current_instantiation = service_instantiation
        # check config for decorators, and add any found
        if 'decorators' in self._service_config.component_config:
            for service_decorator in self._service_config.component_config.get('decorators'):
                try:
                    service_decorator_class = service_instantiation.importclass(
                        service_decorator,
                        self._sys_config('paths', 'emews_pkg_service_decorators_path'))
                except KeyError as ex:
                    self.logger.error("(A key is missing from the config): %s", ex)
                    raise

                current_instantiation = service_decorator_class(current_instantiation)

        return current_instantiation
