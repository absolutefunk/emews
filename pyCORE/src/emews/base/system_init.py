"""
eMews basic system initialization.

Handles initial system initialization tasks, such as config and logging setup, and launches the
system manager.

Created on June 9, 2018
@author: Brian Ricks
"""
import logging
import os
import socket

import emews.base.baseobject
import emews.base.config
import emews.base.importclass
import emews.base.system_manager


def system_init(args, is_daemon=True):
    """
    Init configuration and base system properties.

    If the eMews daemon is launching, then start the SystemManager, otherwise return.
    """
    path_prefix = os.path.join('..', os.path.dirname(os.path.abspath(__file__)))  # root

    # first thing we need to do is parse the configs
    # base system conf (non-user config - system-wide)
    base_config = emews.base.config.parse(os.path.join(path_prefix, 'base/conf.yml'))  # /base
    # system conf (user config - system-)
    system_config = emews.base.config.parse(os.path.join(path_prefix, 'system.yml')) \
        if args.sys_config is None else emews.base.config.parse(
            os.path.join(path_prefix, args.sys_config))
    # node conf (user config - per node)
    node_config = emews.base.config.parse(args.node_config) \
        if args.node_config is not None else {}

    # prepare eMews daemon config dict
    config_start_dict = _merge_configs(
        base_config, system_config, node_config, 'system_config_options')

    # get the node name
    node_name = _get_node_name(config_start_dict, args.node_name)

    # prepare the init dict (only used locally)
    config_init_dict = _merge_configs(
        base_config, system_config, node_config, 'init_config_options')

    # init the logger
    logger = logging.LoggerAdapter(
        _init_base_logger(config_init_dict['logging']), {'nodename': node_name})

    # now we have logging, so we can start outputting though the logger
    logger.debug("Logger initialized.")

    # create system properties
    system_properties = emews.base.config.Config(
        {'logger': logger,
         'node_name': node_name,
         'root': path_prefix})

    # update the BaseObject class var
    emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES = system_properties  # pylint: disable=W0212

    config_obj = emews.base.config.Config(config_start_dict)

    if not is_daemon:
        return config_obj

    return emews.base.system_manager.SystemManager(config_obj)


def _get_node_name(config, arg_name):
    """Determine the node name."""
    # command line arg (top precedence)
    if arg_name is not None:
        return arg_name

    # then config
    node_name = config.get('node_name', None)
    if node_name is not None:
        return node_name

    # default: use host name
    return socket.gethostname()


def _init_base_logger(log_config):
    """Set up the logger."""
    logger_type = log_config['logger']
    message_level = log_config['message_level']

    logger = logging.getLogger(logger_type)
    logger.setLevel(message_level)
    logger.propagate(False)

    for handler_class_path in log_config['log_types'][logger_type]['handlers']:
        handler_class = emews.base.importclass.import_class_from_module(handler_class_path)
        # TODO: Verify handler_options in system.yml to make sure invalid handler options and
        # options which shouldn't be overridden are not processed (ie, throw exception or something)
        handler_options = dict()
        handler_options.update(log_config['log_handlers'][handler_class_path])
        handler_options.update(log_config.get('logger_parameters', {}))

        handler_obj = handler_class(**handler_options)
        handler_obj.setLevel(message_level)
        handler_obj.setFormatter(logging.Formatter(log_config['message_format']))

        logger.addHandler(handler_obj)

    return logger


def _merge_configs(base_config, system_config, node_config, merge_type):
    """
    Merge the input config files by key, in order of precedence.

    Precedence order: base config (if in 'include' section), system config, node config.
    For example, values in node config could override values in system config.
    """
    # start with merged sections from base_config
    merged_conf = dict()

    # Assume top level keys are dicts.
    # All possible sections and kvs are listed under base_config['include_merge']
    for sec, kvs in base_config[merge_type]:
        # start merge
        merged_conf[sec] = dict()
        for s_key, s_val in kvs:
            merged_val = s_val

            # check if in system_config
            config_val = system_config.get(sec, {}).get(s_key, None)
            if config_val is not None:
                # system config overrides this kv
                merged_val = config_val

            # check if in node_config
            config_val = node_config.get(sec, {}).get(s_key, None)
            if config_val is not None:
                # node config overrides this kv
                merged_val = config_val

            # Add config_val to merged_conf if not None (this occurs if val in base_config is None
            # and no other configs override it).
            if merged_val is not None:
                merged_conf[sec][s_key] = merged_val

    return merged_conf
