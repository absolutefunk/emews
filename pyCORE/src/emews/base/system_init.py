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
import sys

import emews.base.config
import emews.base.system_manager


def system_init(args):
    """Init configuration and base system properties."""
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # root
    print "Root path: " + root_path

    # first thing we need to do is parse the configs
    # base system conf (non-user config - system-wide)
    base_config = emews.base.config.parse(os.path.join(root_path, 'base/conf.yml'))
    # system conf (user config - system-wide)
    if args.sys_config is None:
        if args.local:
            system_config = emews.base.config.parse(os.path.join(root_path, 'system_local.yml'))
            print "Starting in local mode."
        else:
            system_config = emews.base.config.parse(os.path.join(root_path, 'system.yml'))
    else:
        system_config = emews.base.config.parse(os.path.join(root_path, args.sys_config))
    # node conf (user config - per node)
    node_config = emews.base.config.parse(args.node_config) \
        if args.node_config is not None else {}

    # merge dicts for init and system dicts
    config_dict_init = emews.base.config.merge_configs(
        base_config['init'], system_config, node_config)
    config_dict_system = emews.base.config.merge_configs(
        base_config['system'], system_config, node_config)

    # get the node name and id
    node_name = _get_node_name(config_dict_init['general']['node_name'], args.node_name)
    node_id = 0

    # init the logger
    logger = logging.LoggerAdapter(
        _init_base_logger(config_dict_init['logging']), {'nodename': node_name, 'nodeid': node_id})

    # now we have logging, so we can start outputting though the logger
    logger.debug("Logger initialized.")

    # create system properties
    sysprop = emews.base.config.SysProp(
        _logger=logger,
        _node_name=node_name,
        _node_id=node_id,
        _root_path=root_path,
        _local=args.local)

    return emews.base.system_manager.SystemManager(config_dict_system, sysprop)


def _get_node_name(config_node_name, arg_name):
    """Determine the node name."""
    # command line arg (top precedence)
    if arg_name is not None:
        return arg_name

    # then config
    if config_node_name is not None:
        return config_node_name

    # default: use host name
    return socket.gethostname()


def _init_base_logger(log_config):
    """Set up the logger."""
    message_level = log_config['message_level']

    logger = logging.getLogger(log_config['logger_name'])
    logger.setLevel(message_level)
    logger.propagate = False

    logger_enabled = False
    if log_config['file']:
        # log to a file
        handler_obj = logging.FileHandler(mode='a', delay=True, filename=log_config['file'])
        handler_obj.setLevel(message_level)
        handler_obj.setFormatter(logging.Formatter(log_config['message_format']))
        logger.addHandler(handler_obj)
        logger_enabled = True

    if log_config['stream']:
        # log to a stream
        stream_path, stream_name = log_config['stream'].rsplit(".", 1)

        handler_obj = logging.StreamHandler(stream=getattr(sys.modules[stream_path], stream_name))
        handler_obj.setLevel(message_level)
        handler_obj.setFormatter(logging.Formatter(log_config['message_format']))
        logger.addHandler(handler_obj)
        logger_enabled = True

    if not logger_enabled:
        # logging disabled
        print "No file or stream specified for logging.  Logging disabled (no output) ..."
        logger.addHandler(logging.NullHandler())

    return logger
