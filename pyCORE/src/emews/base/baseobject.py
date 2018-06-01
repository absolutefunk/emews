'''
BaseObject: the base of everything (well, almost...)
This class implements stuff that is common to almost everything class in emews: logging,
configuration, et al.

Created on Apr 9, 2018

@author: Brian Ricks
'''
import logging

import emews.base.importclass
import emews.base.configcomponent

class BaseObject(object):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        config is the Config required, which contains the logger and configuration
        (system configuration, object configuration...)
        The config object is cloned, and the original config object not referenced.
        '''
        self._logger = logging.LoggerAdapter(logging.getLogger(
            config.get_sys('logging', 'main_logger')), {'nodename': config.nodename})

        if config.component_config is not None:
            self._config = config.get_new('config')  # 'config' key required

            # instantiate any dependencies
            if 'dependencies' in self._config.component_config:
                self._dependencies = self.instantiate_dependencies(self._config.get('dependencies'))
            else:
                self._dependencies = None

        else:
            # self._logger.debug("No object configuration information found.")
            self._config = config  # no component config

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

    @property
    def dependencies(self):
        '''
        @Override returns the dependencies of this service, or None if none are defined.
        Convenience method.
        '''
        return self._dependencies

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

            # check optional params
            b_instantiate = True
            if 'instantiate' in dependency:
                if not isinstance(dependency['instantiate'], bool):
                    raise ValueError(
                        "Key 'instantiate' must have a boolean value (given value: %s)." %
                        str(dependency['instantiate']))
                else:
                    b_instantiate = dependency['instantiate']

            try:
                class_object = emews.base.importclass.import_class_from_module(
                    class_name, class_path)
            except ImportError as ex:
                self.logger.error("Could not import dependency '%s': %s",
                                  dep_name, ex)
                raise

            # If the dependency has config options, then clone a new config object with it,
            # otherwise just clone with none.
            if 'config' in dependency:
                dep_config = self._config.clone_with_dict(dependency['config'])
            else:
                dep_config = self._config.clone_with_config(None)

            if b_instantiate:
                try:
                    dependency_instantiation_dict[dep_name] = class_object(dep_config)
                except AttributeError as ex:
                    self.logger.error("Dependency '%s' could not be instantiated: %s", dep_name, ex)
                    raise
                self.logger.debug("Dependency '%s' instantiated.", dep_name)
            else:
                # instantiation not requested
                dependency_instantiation_dict[dep_name] = {
                    'class': class_object,
                    'config': dep_config
                }

        return emews.base.configcomponent.ConfigComponent(dependency_instantiation_dict)
