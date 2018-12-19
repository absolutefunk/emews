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
    logger_type = log_config['logger']
    message_level = log_config['message_level']

    logger = logging.getLogger(logger_type)
    logger.setLevel(message_level)
    logger.propagate = False

    print "Using logger: " + str(logger_type)

    for handler_class_path in log_config['log_types'][logger_type]['handlers']:
        handler_class = emews.base.importclass.import_class_from_module(handler_class_path)
        # TODO: Verify handler_options in system.yml to make sure invalid handler options and
        # options which shouldn't be overridden are not processed (ie, throw exception or something)
        handler_options = {}
        handler_options.update(log_config['log_handlers'][handler_class_path])

        if handler_class_path == 'logging.StreamHandler':
            # StreamHandler requires a reference to the stream, so we need to take care of that.
            try:
                stream_path, stream_name = log_config['logger_parameters']['stream'].rsplit(".", 1)
            except KeyError as ex:
                raise KeyError("%s requires logger_parameters key: %s"
                               % (str(logger_type), str(ex)))

            handler_options['stream'] = getattr(sys.modules[stream_path], stream_name)
        else:
            handler_options.update(log_config['logger_parameters'])

        handler_obj = handler_class(**handler_options)
        handler_obj.setLevel(message_level)
        handler_obj.setFormatter(logging.Formatter(log_config['message_format']))

        logger.addHandler(handler_obj)

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

def _section_merge(sec1, sec2):
    """
    Merge the first section with the second section given.  A section is a dict.

    This is a recursive procedure; the section depth should not be that great.
    """
    new_section = {}
    for s_key, s_val in sec1.iteritems():
        if isinstance(s_val, collections.Mapping):
            # s_val is a dict (section)
            # We require that if a section is present at s_key in sec1, then if sec2 has this
            # key present, then it must also be a section or None, which is just shorthand for an
            # empty dict.
            if sec2.get(s_key, None) is not None:
                if not isinstance(sec2[s_key], collections.Mapping):
                    raise KeyError("Base configuration requires key '%s' to be a section (map)." % s_key)
                elif not s_val or 'emews-overwrite' in s_val:
                    # empty dict in sec1 or 'emews-overwrite' key is present
                    new_section[s_key] = _section_merge(sec2[s_key], {})
                    new_section[s_key]['emews-overwrite'] = True
                else:
                    new_section[s_key] = _section_merge(s_val, sec2[s_key])
            else:
                # We don't simply assign s_val here, as we don't know which dict implementation it
                # is.  This way the resulting config object consists of plain dicts.
                new_section[s_key] = _section_merge(s_val, {})
        elif s_key in sec2:
            # s_val is not a dict, s_key present in sec2
            if s_val is not None and not isinstance(s_val, sec2[s_key].__class__):
                raise ValueError("Type mismatch of config value for key '%s'. Must be %s." % (s_key, type(s_val)))
            new_section[s_key] = sec2[s_key]
        else:
            # s_val is not a dict, s_key not present in sec2
            new_section[s_key] = s_val

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
