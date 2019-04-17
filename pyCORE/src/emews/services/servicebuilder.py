"""
Builder for services.  Handles things such as configuration and which service to actually build.

Created on Apr 2, 2018
@author: Brian Ricks
"""
import collections
import os

import emews.base.config
import emews.base.import_tools
import emews.base.serv_hub
import emews.components.importer
import emews.components.samplers.zerosampler


class ServiceBuilder(object):
    """classdocs."""

    __slots__ = ('_sys', '_service_count')

    def __init__(self, sysprop):
        """Constructor."""
        self._sys = sysprop
        self._service_count = {}  # mapping from service class to instantiation count

    def build(self, service_name, service_config_dict=None, service_config_file=None):
        """Build the service."""
        if service_config_dict is not None:
            # checks
            if not isinstance(service_config_dict, collections.Mapping):
                err_str = "Service configuration passed as argument is not a dictionary."
                self._sys.logger.error(err_str)
                raise AttributeError(err_str)
            if 'parameters' not in service_config_dict:
                err_str = "Service configuration passed as argument missing required section " \
                          "'parameters'."
                self._sys.logger.error(err_str)
                raise AttributeError(err_str)

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

        # -- configure execution --
        service_loop = None
        if 'execution' in service_config:
            # looping
            if service_config['execution'].get('loop', False):
                # assume loop_config is a properly formatted dict
                if 'loop_using_sampler' in service_config['execution']:
                    service_loop = emews.components.importer.instantiate(
                        service_config['execution']['loop_using_sampler'])
                else:
                    service_loop = emews.components.samplers.zerosampler.ZeroSampler()

        local_service_id = self._service_count.get(service_name, -1) + 1
        service_id = self._get_service_id(local_service_id)
        service_name_full = service_name + '_' + str(local_service_id)
        self.logger.debug("Service '%s' assigned id '%d'.", service_name_full, service_id)

        # inject dict
        service_config_inject = {}
        service_config_inject['service_name'] = service_name_full
        service_config_inject['local_service_id'] = local_service_id
        service_config_inject['service_id'] = service_id
        service_config_inject['_service_loop'] = service_loop
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

        self._service_count[service_name] = local_service_id

        return service_obj

    def _get_service_id(self, local_service_id):
        """Get a globally unique service id."""
        if self._sys.local:
            # there is no global id in local mode
            return local_service_id

        return self.sys.net.hub_query(emews.base.serv_hub.HubProto.HUB_SERVICE_ID_REQ)
