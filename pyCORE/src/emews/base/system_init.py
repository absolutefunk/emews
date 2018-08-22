'''
Handles initial system initialization tasks, such as config and logging setup.
Launches the system manager.

Created on June 9, 2018
@author: Brian Ricks
'''
import logging
import os
import socket

import emews.base.config
import emews.base.importclass
import emews.base.system_manager

def system_init(args):
    '''
    Inits the eMews daemon.
    '''
    # first thing we need to do is parse the configs
    # base system conf (non-user config - global)
    base_config = emews.base.config.parse("conf.yml")  # conf.yml in same directory as this
    # system conf (user config - global)
    system_config = emews.base.config.parse(os.path.join("..", "system.yml")) \
        if args.sys_config is None else emews.base.config.parse(args.sys_config)
    # node conf (user config - per node)
    node_config = emews.base.config.parse(args.node_config)

    # get the node name
    node_name = _get_node_name(system_config['general'], node_config.get('general', {}),
                               args.node_name)
    # init the logger
    logger = logging.LoggerAdapter(
        _init_base_logger(base_config['logging'], system_config['logging'], node_config['logging']),
        {'nodename': node_name})

    # now we have logging, so we can start outputting though the logger
    logger.debug("Logger initialized.")

    # prepare config dict
    config_start_dict = dict()
    config_start_dict['config'] = _merge_configs(
        base_config, system_config, node_config, logger=logger)

    # create system options
    system_options = {
        'node_name': node_name,
        'logger': logger
    }

    return emews.base.system_manager.SystemManager(
        emews.base.config.Config(config_start_dict, system_options))

def _get_node_name(system_config, node_config, arg_name):
    '''
    Determines the node name.
    '''
    # command line arg (top precedence)
    if arg_name is not None:
        return arg_name

    # then node config
    node_name = node_config.get('node_name', None)
    if node_name is not None:
        return node_name

    # then system config
    node_name = system_config.get('node_name', None)
    if node_name is not None:
        return node_name

    # default: use host name
    return socket.gethostname()

def _init_base_logger(base_config, system_config, node_config):
    '''
    Sets up the logger.
    '''
    logger_type = system_config.get('logger', base_config['logger'])
    message_level = system_config.get('message_level', base_config['message_level'])

    logger = logging.getLogger(logger_type)
    logger.setLevel(message_level)
    logger.propagate(False)

    for handler_class_path in base_config['log_types'][logger_type]['handlers']:
        handler_class = emews.base.importclass.import_class_from_module(handler_class_path)
        #TODO: Verify handler_options in system.yml to make sure invalid handler options and options
        # which shouldn't be overridden are not processed (ie, throw exception or something).
        handler_options = dict()
        handler_options.update(base_config['log_handlers'][handler_class_path])
        handler_options.update(system_config.get('logger_parameters', {}))

        handler_obj = handler_class(**handler_options)
        handler_obj.setLevel(message_level)
        handler_obj.setFormatter(logging.Formatter(base_config['message_format']))

        logger.addHandler(handler_obj)

    return logger

def _merge_configs(base_config, system_config, node_config, logger=None):
    '''
    Merges the input config files by key, in order of precedence (base config- if in 'include'
    section, system config, node config).
    Values in node config could override values in system config.
    '''
    # start with merged sections from base_config
    merged_conf = dict()

    # Assume top level keys are dicts.
    # All possible sections and kvs are listed under base_config['include_merge']
    for sec, kvs in base_config['system_config_options']:
        # start merge
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
                if not sec in merged_conf:
                    merged_conf[sec] = dict()
                merged_conf[sec][s_key] = merged_val

        # adds the required sections, if they are not already present
        _add_required_sections(base_config, merged_conf)

    return merged_conf

def _add_required_sections(base_config, config):
    '''
    Checks for and adds (empty) sections that are missing from the input config file.
    base_config contains a list of required sections.
    '''
    for section_name, _ in base_config['required_sections']:
        if section_name in config:
            continue

        config[section_name] = None
