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
import struct
import sys
import threading

import emews.base.enums
import emews.base.config
import emews.base.logger
import emews.base.serv_hub
import emews.base.system_manager
import emews.base.sysprop


def system_init(args):
    """Init configuration and base system properties."""
    root_path = emews.base.config.get_root_path()
    print "[system_init] Root path: " + root_path

    # first thing we need to do is parse the configs
    # base system conf (non-user config - system-wide)
    base_config = emews.base.config.parse(os.path.join(root_path, 'base/conf.yml'))
    # system conf (user config - system-wide)
    if args.sys_config is None:
        if args.local:
            system_config = emews.base.config.parse(os.path.join(root_path, 'system_local.yml'))
            print "[system_init] Starting in local mode."
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

    node_name = _get_node_name(config_dict_init['general']['node_name'],
                               args.node_name,
                               config_dict_init['general']['node_name_length'])
    is_hub = True if node_name == config_dict_system['hub']['node_name'] and not args.local \
        else False

    print "[system_init] Node name: " + str(node_name) + "."
    sys.stdout.flush()

    if config_dict_system['general']['system_start_delay'] > 0:
        # wait the given amount of time to proceed
        if is_hub:
            print "[system_init] System start delay is given, but we are the hub, so ignoring ... "
            sys.stdout.flush()
        else:
            local_wait_event = threading.Event()

            print "[system_init] Waiting " + \
                str(config_dict_system['general']['system_start_delay']) + " seconds to proceed ..."
            sys.stdout.flush()
            try:
                local_wait_event.wait(config_dict_system['general']['system_start_delay'])
            except KeyboardInterrupt:
                print "[system_init] Caught interrupt ..."
                sys.stdout.flush()
                return None

    if is_hub or args.local:
        node_id = 1  # hub or local mode node id
        log_host = '127.0.0.1'  # not used in local mode
    else:
        # The node id is assigned by the hub node.
        # Once node id is assigned, this node will use it whenever connecting to the hub.
        try:
            if config_dict_system['hub']['node_address'] is None:
                # hub address is not provided to us in the config
                print "[system_init] Hub node address is not given in the config."
                sys.stdout.flush()
                config_dict_system['hub']['node_address'] = \
                    _listen_hub(config_dict_system['communication']['port'],
                                config_dict_init['communication']['hub_broadcast_wait'],
                                config_dict_init['communication']['hub_broadcast_max_attempts'],
                                config_dict_init['general']['node_name_length'],
                                config_dict_system['hub']['node_name'])

            print "[system_init] Hub node address: " + str(config_dict_system['hub']['node_address'])
            sys.stdout.flush()

            node_id = _get_node_id(config_dict_system['hub']['node_address'],
                                   config_dict_system['communication']['port'],
                                   config_dict_system['communication']['connect_timeout'],
                                   config_dict_system['communication']['connect_max_attempts'])
        except IOError as ex:
            print "[system_init] " + str(ex)
            sys.stdout.flush()
            return None
        except KeyboardInterrupt:
            return None

        log_host = config_dict_system['hub']['node_address']

    print "[system_init] Node id: " + str(node_id) + "."
    sys.stdout.flush()

    emews.base.logger._base_logger = logging.LoggerAdapter(
        _init_base_logger(
            config_dict_init['logging'],
            node_id,
            log_host,
            config_dict_system['communication']['port'],
            is_hub=is_hub,
            is_local=args.local),
        {'nodename': node_name, 'nodeid': node_id})

    print "[system_init] Logging instantiated."
    sys.stdout.flush()

    sysprop_dict = {
        'node_name': node_name,
        'node_id': node_id,
        'root_path': root_path,
        'is_hub': is_hub,
        'local': args.local
    }

    return emews.base.system_manager.SystemManager(config_dict_system,
                                                   emews.base.sysprop.SysProp(**sysprop_dict))


def _get_node_name(config_node_name, arg_name, max_length):
    """Determine the node name."""
    # if-else in order of name source precedence
    if arg_name is not None:
        node_name = arg_name
    elif config_node_name is not None:
        node_name = config_node_name
    else:
        node_name = socket.gethostname()

    return node_name[:max_length] if len(node_name) > max_length else node_name


def _listen_hub(port, timeout, max_attempts, buf_size, hub_name):
    """Listen for a broadcast from the hub node to obtain address."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP sock
    sock.bind(('0.0.0.0', port))
    sock.settimeout(timeout)
    recv_attempts = 0
    print "[system_init] Network routers must be configured to properly forward broadcast messages."

    while recv_attempts < max_attempts:
        print "[system_init] Listening for broadcast from hub node (attempt " + \
            str(recv_attempts + 1) + "\\" + str(max_attempts) + ", timeout per attempt: " + \
            str(timeout) + "s) ..."
        sys.stdout.flush()

        try:
            chunk, addr = sock.recvfrom(buf_size)

            print "[system_init] Received from " + str(addr[0]) + ": " + str(chunk)
            if chunk != hub_name:
                print "[system_init] Node name '" + str(chunk) + "' does not match hub name."
                recv_attempts += 1
                continue

        except socket.error:
            recv_attempts += 1
            continue
        except KeyboardInterrupt:
            print "[system_init] Caught interrupt ..."
            sys.stdout.flush()
            sock.close()
            raise

        break

    sock.close()
    if recv_attempts == max_attempts:
        # could not recv a broadcast from the hub node
        raise IOError("Did not receive broadcast from hub node.")

    print "[system_init] Hub node address: " + str(addr[0])
    sys.stdout.flush()
    return addr[0]


def _get_node_id(addr, port, timeout, max_attempts):
    """Connect to the address given (assuming to be the hub node) to obtain the node id."""
    connect_attempts = 0

    while connect_attempts < max_attempts:
        print "[system_init] Attempting to obtain node id from hub node (attempt " + \
            str(connect_attempts + 1) + "\\" + str(max_attempts) + ", timeout per attempt: " + \
            str(timeout) + "s) ..."
        sys.stdout.flush()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((addr, port))
            sock.sendall(struct.pack('>HLHL',
                                     emews.base.enums.net_protocols.NET_HUB,
                                     0,  # node id (not assigned yet, so leave at zero),
                                     emews.base.enums.hub_protocols.HUB_NODE_ID_REQ,
                                     0  # params (none)
                                     ))
            chunk = sock.recv(4)  # node_id (4 bytes)
            node_id = struct.unpack('>L', chunk)[0]
        except (socket.error, struct.error):
            connect_attempts += 1
            sock.close()
            continue
        except KeyboardInterrupt:
            print "[system_init] Caught interrupt ..."
            sys.stdout.flush()
            sock.close()
            raise

        break

    sock.close()

    if connect_attempts == max_attempts:
        # could not get the node id
        raise IOError("Could not obtain a node id from hub node.")

    return node_id


def _init_base_logger(log_config, node_id, host, port, is_hub=False, is_local=False):
    """Set up the logger."""
    logger = logging.getLogger(log_config['logger_name'])
    logger.setLevel(log_config['message_level'])
    logger.propagate = False

    if is_local:
        # local mode: log to a stream (stdout)
        _log_handler_stream(log_config, logger)
    elif is_hub:
        # hub node
        if log_config['output'] == 'console':
            _log_handler_stream(log_config, logger)
        elif log_config['output'] == 'file':
            _log_handler_file(log_config, logger)
        else:
            print "[system_init] Logger output '" + str(log_config['output']) + \
                "' not supported, defaulting to console."
            sys.stdout.flush()
            _log_handler_stream(log_config, logger)
    else:
        # non-hub node: distributed logging
        logger.addHandler(emews.base.logger.DistLogger(host, port, node_id))

    return logger


def _log_handler_stream(log_config, logger):
    """Log to a stream."""
    stream_path, stream_name = log_config['stream'].rsplit(".", 1)

    handler_obj = logging.StreamHandler(stream=getattr(sys.modules[stream_path], stream_name))
    handler_obj.setLevel(log_config['message_level'])
    handler_obj.setFormatter(logging.Formatter(log_config['message_format']))
    logger.addHandler(handler_obj)


def _log_handler_file(log_config, logger):
    """Log to a file."""
    handler_obj = logging.FileHandler(mode='a', delay=True, filename='emews.log')
    handler_obj.setLevel(log_config['message_level'])
    handler_obj.setFormatter(logging.Formatter(log_config['message_format']))
    logger.addHandler(handler_obj)
