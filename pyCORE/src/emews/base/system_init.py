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


def system_init(args):
    """Init configuration and base system properties."""
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
        'system_config_options', base_config, system_config, node_config)

    # prepare the init dict (only used locally)
    config_init_dict = _merge_configs(
        'init_config_options', base_config, system_config, node_config)

    if args.local:
        # local mode
        # merge the local overrides
        config_start_dict = _merge_configs(
            None, config_start_dict, config_start_dict.get('local', {}))
        config_init_dict = _merge_configs(None, config_init_dict, config_init_dict.get('local', {}))

    # get the node name
    node_name = _get_node_name(config_start_dict, args.node_name)

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

    # remove the local section from the config_start_dict
    del config_start_dict['local']

    return emews.base.system_manager.SystemManager(
        emews.base.config.Config(config_start_dict), local_mode=args.local)


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


def _merge_configs(merge_type, *config_dicts):
    """
    Merge the input config files by key, in order of precedence.

    Precedence order: base config, system config, node config.
    For example, values in node config could override values in system config.
    """
    if len(config_dicts) < 2:
        # must be at least two dicts to merge
        raise ValueError("At least two dicts must be passed.")

    first_dict = True
    merged_dict = None
    for config_dict in config_dicts:
        if first_dict:
            first_dict = False
            # first dict is assumed to be the base config dict
            if merge_type is None:
                merged_dict = config_dict
            else:
                merged_dict = config_dict[merge_type]
            continue

        merged_dict = _section_merge(merged_dict, config_dict)

    return merged_dict

def _section_merge(sec1, sec2, merge_both=False):
    """
    Merge the first section with the second section given.  A section is a dict.

    This is a recursive procedure; the section depth should not be that great.  If merge_both is
    true, then merge into the final dict any K/Vs from sec2 that are not in sec1.  This situation
    arises when the base config skeleton contains an empty dict, meaning that the contents could
    vary.
    """
    new_section = {}
    for s_key, s_val in sec1:
        if isinstance(s_val, dict):
            # s_val is a dict (section)
            # We require that if a section is present at s_key in sec1, then if sec2 has this
            # key present, then it must also be a section.
            if s_key in sec2:
                if not isinstance(sec2[s_key], dict):
                    raise KeyError("Base configuration requires key '%s' to be a section.")
                # If the dict (s_val) is empty, then a special case arises in which the content of
                # the section is undefined.  In this case, we need to merge from both sections,
                # instead of just sec1.
                if merge_both or not s_val:
                    # If merge_both is true, then we are already in the special case.  If s_val is
                    # empty, then the special case is required.  Note that if s_val is not empty
                    # but sec2[s_key] is an empty dict, then the special case (merge_both) is not
                    # invoked, unless we are already in the special case, which essentially will
                    # have no effect.
                    new_section[s_key] = _section_merge(s_val, sec2[s_key], merge_both=True)
                else:
                    new_section[s_key] = _section_merge(s_val, sec2[s_key])
            else:
                # s_key not present in sec2
                new_section[s_key] = s_val
        elif s_key in sec2:
            # s_val is not a dict, s_key present in sec2
            new_section[s_key] = sec2[s_key]
        else:
            # s_val is not a dict, s_key not present in sec2
            new_section[s_key] = s_val

    if merge_both:
        # Merge from sec2.  This will only be those keys not present in sec1.
        for s_key, s_val in sec2:
            if s_key not in new_section:
                # Here we don't care what s_val is, as s_key is not present.
                new_section[s_key] = s_val

    return new_section
