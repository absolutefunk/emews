"""
eMews basic system initialization.

Handles initial system initialization tasks, such as config and logging setup, and launches the
system manager.

Created on June 9, 2018
@author: Brian Ricks
"""
import collections
import logging
import os
import socket
import sys

import emews.base.baseobject
import emews.base.config
import emews.base.importclass
import emews.base.system_manager


def system_init(args):
    """Init configuration and base system properties."""
    path_prefix = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))  # root
    #path_prefix = os.path.abspath(os.path.join(path_prefix, os.pardir))  # root
    print "Root path: " + path_prefix

    # first thing we need to do is parse the configs
    # base system conf (non-user config - system-wide)
    base_config = emews.base.config.parse(os.path.join(path_prefix, 'base/conf.yml'))
    # system conf (user config - system-wide)
    if args.sys_config is None:
        if args.local:
            system_config = emews.base.config.parse(os.path.join(path_prefix, 'system_local.yml'))
        else:
            system_config = emews.base.config.parse(os.path.join(path_prefix, 'system.yml'))
    else:
        system_config = emews.base.config.parse(os.path.join(path_prefix, args.sys_config))
    # node conf (user config - per node)
    node_config = emews.base.config.parse(args.node_config) \
        if args.node_config is not None else {}

    # prepare eMews daemon config dict
    config_start_dict = _merge_configs(
        'system_config_options', base_config, system_config, node_config)

    # prepare the init dict (only used locally)
    config_init_dict = _merge_configs(
        'init_config_options', base_config, system_config, node_config)

    # get the node name
    node_name = _get_node_name(config_start_dict['general'], args.node_name)

    # init the logger
    logger = logging.LoggerAdapter(
        _init_base_logger(config_init_dict['logging']), {'nodename': node_name})

    # now we have logging, so we can start outputting though the logger
    logger.debug("Logger initialized.")

    # create system properties
    system_properties = emews.base.config.Config(
        {'logger': logger,
         'node_name': node_name,
         'root': path_prefix,
         'local': args.local})

    # update the BaseObject class var
    emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES = system_properties  # pylint: disable=W0212

    return emews.base.system_manager.SystemManager(
        emews.base.config.Config(config_start_dict))


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

# TODO: Move this to config.py!!
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
    readonly_dict = None
    for config_dict in config_dicts:
        if first_dict:
            first_dict = False
            # first dict is assumed to be the base config dict
            merged_dict = config_dict[merge_type]['overrides']
            readonly_dict = config_dict[merge_type]['readonly']
            continue

        merged_dict = _section_merge(merged_dict, config_dict)

    # add in the read-only options
    _section_update_readonly(readonly_dict, merged_dict)
    return merged_dict

def _section_merge(sec1, sec2, keychain="root"):
    """
    Merge the first section with the second section given.  A section is a dict.

    This is a recursive procedure; the section depth should not be that great.
    """
    new_section = {}

    for s1_key, s1_val in sec1.iteritems():
        s2_val = sec2.get(s1_key, None)  # if sec2 doesn't contain s1_key, or s1_key is None

        if isinstance(s1_val, collections.Mapping):
            # s1_val is a section
            cur_kc = keychain + str(s1_key)

            if not isinstance(s2_val, collections.Mapping):
                raise TypeError("While parsing configuration at %s: Attempted override of section with a non-section type." % cur_kc)

            if s2_val is None:
                # this ensures the resulting section is a basic dict
                new_section[s1_key] = _section_merge(s1_val, {}, keychain=cur_kc)
            else:
                new_section[s1_key] = _section_merge(s1_val, s2_val, keychain=cur_kc)

        elif s2_val is not None:
            if s1_val is not None and not isinstance(s1_val, s2_val.__class__):
                # if s1_val is None, then just overwrite it with s2_val
                raise ValueError("Type mismatch of config value for key '%s'. Must be %s." % (s_key, type(s_val)))

            new_section[s1_key] = s2_val
        else:
            # s1_val not a section and s1_key either not present in sec2 or s2_val is None
            new_section[s1_key] = s1_val

    return new_section

def _section_update_readonly(readonly_sec, merged_sec):
    """
    Add the readonly keys to the merged dict.

    This is a recursive procedure; the section depth should not be that great.
    """
    for s_key, s_val in readonly_sec.iteritems():
        if isinstance(s_val, collections.Mapping):
            # s_val is a dict (section)
            if s_key not in merged_sec:
                merged_sec[s_key] = {}
            _section_update_readonly(s_val, merged_sec[s_key])
        else:
            if merged_sec.get(s_key, None) is not None:
                raise ValueError("Cannot override values of read-only keys.  Key: '%s'." % s_key)
            merged_sec[s_key] = s_val
