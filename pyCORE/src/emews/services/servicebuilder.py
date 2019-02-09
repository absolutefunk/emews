"""
Builder for services.  Handles things such as configuration and which service to actually build.

Created on Apr 2, 2018
@author: Brian Ricks
"""
import collections
import os

import emews.base.config
import emews.base.import_tools


class ServiceBuilder(object):
    """classdocs."""

    __slots__ = ('_sys')

    def __init__(self, sysprop):
        """Constructor."""
        self._sys = sysprop

    def build(self, service_name, service_config_dict=None, service_config_file=None):
        """Build the service."""
        if service_config_dict is not None:
            service_config = service_config_dict
            self._sys.logger.debug("Using service configuration passed as argument.")
        else:
            if service_config_file is None:
                service_config_file = service_name.lower() + ".yml"

            service_config_path = os.path.join(
                self._sys.root_path, "services", service_name.lower(), service_config_file)

            try:
                service_config = emews.base.config.parse(service_config_path)
            except IOError:
                self._sys.logger.error("Could not load service configuration: %s",
                                       service_config_path)
                raise

            self._sys.logger.debug("Loaded service configuration: %s", service_config_path)

        # import service module
        try:
            service_class = emews.base.import_tools.import_service(service_name)
        except ImportError:
            self._sys.logger.error("Service module '%s' could not be imported.", service_name)
            raise

        # TODO: Add global service identifiers (will need to have a central server for this)

        # inject dict
        service_config_inject = {}
        service_config_inject['service_name'] = service_name
        service_config_inject['service_id'] = -1  # TODO: set this to the actual service id (global)
        service_config_inject['_sys'] = self._sys
        service_config_inject['logger'] = self._sys.logger

        # instantiate service object
        try:
            service_obj = service_class(service_config['parameters'],
                                        _inject=service_config_inject)
            self._sys.logger.debug("Service class '%s' instantiated.", service_name)
        except StandardError:
            self._sys.logger.error("Service '%s' could not be instantiated.", service_name)
            raise

        service_exec_config = service_config.get('execution', None)

        # build service modifiers
        return (service_obj, service_exec_config)
