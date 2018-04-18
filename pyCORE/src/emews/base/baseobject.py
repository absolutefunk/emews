'''
BaseObject: the base of everything (well, almost...)
This class implements stuff that is common to almost everything class in emews: logging,
configuration, et al.

Created on Apr 9, 2018

@author: Brian Ricks
'''
import logging

import emews.base.importclass

class BaseObject(object):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        config is the Config required, which contains the logger and configuration
        (system configuration, object configuration...)
        '''
        self._config = config
        self._logger = logging.LoggerAdapter(logging.getLogger(
            self._config.get_sys('logging', 'base_logger')), {'nodename': self._config.nodename})

    @property
    def logger(self):
        '''
        returns the logger object
        '''
        return self._logger

    @property
    def config(self):
        '''
        returns the configuration object
        '''
        return self._config

    def instantiate_dependencies(self, deps_config):
        '''
        For each dependency in the supplied dict, attempt to instantiate the dependency.
        '''
        dependency_instantiation_dict = dict()
        for dep_name, dependency in deps_config.iteritems():
            self.logger.debug("Resolving dependency '%s'.", dep_name)
            try:
                class_name = dependency['class']
                class_path = dependency['module']
            except KeyError as ex:
                self.logger.error("Required key missing from configuration for dependency '%s': %s",
                                  dep_name, ex)
                raise
            try:
                class_object = emews.base.importclass.import_class_from_module(
                    class_name, class_path)
            except ImportError as ex:
                self.logger.error("Could not import dependency '%s': %s",
                                  dep_name, ex)
                raise

            # if the dependency has config options, then clone a new config object with it
            if 'config' in dependency:
                dep_config = self._config.clone_with_dict(dependency['config'])
                self.logger.debug("Found config information for '%s'.", dep_name)
            else:
                dep_config = None
                self.logger.debug("No config information found for '%s'.", dep_name)

            try:
                dependency_instantiation_dict[dep_name] = class_object(dep_config)
            except AttributeError as ex:
                self.logger.error("Dependency '%s' could not be instantiated: %s", dep_name, ex)
                raise
            self.logger.debug("Dependency '%s' instantiated.", dep_name)

        return dependency_instantiation_dict
