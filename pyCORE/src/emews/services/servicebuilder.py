"""
Builder for services.  Handles things such as configuration and which service to actually build.

Created on Apr 2, 2018
@author: Brian Ricks
"""
import collections
import os

import emews.base.baseobject
import emews.base.config
import emews.base.enums
import emews.base.import_tools
import emews.components.samplers.zerosampler


class ServiceBuilder(emews.base.baseobject.BaseObject):
    """classdocs."""

    __slots__ = ('_service_count', '_net_client')

    def __init__(self):
        """Constructor."""
        super(ServiceBuilder, self).__init__()

        self._service_count = {}  # mapping from service class to instantiation count

    def build(self, service_name, service_config_dict=None, service_config_file=None):
        """Build the service."""
        if service_config_dict is not None:
            # checks
            if not isinstance(service_config_dict, collections.Mapping):
                err_str = "Service configuration (dict arg) is not a dictionary."
                self.logger.error(err_str)
                raise AttributeError(err_str)
            if 'parameters' not in service_config_dict:
                err_str = "Service configuration (dict arg) missing required section: parameters."
                self.logger.error(err_str)
                raise AttributeError(err_str)

            service_config = service_config_dict
            self.logger.debug("Using service configuration passed as argument.")
        else:
            if service_config_file is None:
                service_config_file = service_name.lower() + ".yml"

            service_config_path = os.path.join(
                self.sys.root_path, "services", service_name.lower(), service_config_file)

            try:
                service_config = emews.base.config.parse(service_config_path)
            except IOError:
                self.logger.error("Could not load service configuration: %s", service_config_path)
                raise

            if 'parameters' not in service_config:
                err_str = "Service configuration (from file) missing required section: parameters."
                self.logger.error(err_str)
                raise AttributeError(err_str)

            self.logger.debug("Loaded service configuration: %s", service_config_path)

        # import service module
        try:
            service_class = emews.base.import_tools.import_service(service_name)
        except ImportError:
            self.logger.error("Service module '%s' could not be imported.", service_name)
            raise

        # -- configure execution --
        service_loop = None
        if 'execution' in service_config:
            # looping
            if service_config['execution'].get('loop', False):
                # assume loop_config is a properly formatted dict
                if 'loop_using_sampler' in service_config['execution']:
                    service_loop = self.sys.import_component(
                        service_config['execution']['loop_using_sampler'])
                else:
                    service_loop = emews.components.samplers.zerosampler.ZeroSampler()

        local_service_id = self._service_count.get(service_name, -1) + 1
        service_id = self._get_service_id(local_service_id)
        service_name_full = service_name + '_' + str(local_service_id)
        self.logger.debug("Service '%s' assigned service id: %d", service_name_full, service_id)

        # inject dict
        service_config_inject = {}
        service_config_inject['service_name'] = service_name_full
        service_config_inject['local_service_id'] = local_service_id
        service_config_inject['service_id'] = service_id
        service_config_inject['_service_loop'] = service_loop
        service_config_inject['_sys'] = self.sys
        service_config_inject['logger'] = self.logger

        # instantiate service object
        try:
            service_obj = service_class(service_config['parameters'],
                                        _inject=service_config_inject)
            self.logger.debug("Service class '%s' instantiated.", service_name)
        except StandardError:
            self.logger.error("Service '%s' could not be instantiated.", service_name)
            raise

        self._service_count[service_name] = local_service_id

        return service_obj

    def _get_service_id(self, local_service_id):
        """Get a globally unique service id."""
        if self.sys.local:
            # there is no global id in local mode
            return local_service_id

        return self._net_client.hub_query(emews.base.enums.hub_protocols.HUB_SERVICE_ID_REQ)
