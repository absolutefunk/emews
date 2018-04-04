'''
Builder for services.  Handles things such as configuration and which service to actually build.

Created on Apr 2, 2018

@author: Brian Ricks
'''
import ConfigParser
import importlib

import emews.core.config

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
        self._service_module = None

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
        # Attempt to resolve the module.  If using pyCORE naming, then service should also resolve.
        try:
            self._service_module = importlib.import_module(val_service_name.lowercase(),
                                                           self._sys_config.get_sys(
                                                               'PYCORE_PKG_SERVICES_PATH'))
        except ImportError as ex:
            self.logger.error("Service name could not be resolved into a module.")
            self.logger.debug(ex)
            raise

        try:
            self._service_class = getattr(self._service_module, val_service_name)
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
            self._config = emews.core.config.parse(emews.core.config.prepend_path(val_config_path))
        except ConfigParser.Error as ex:
            self.logger.error("Service configuration could not be parsed.")
            self.logger.debug(ex)
            raise

    def __build_service(self):
        '''
        builds the service
        '''

        try:
            service_instantiation =  self._service_class()
        except StandardError as ex:
            self.logger.error("Service class could not be instantiated.")
            self.logger.debug(ex)
            raise
