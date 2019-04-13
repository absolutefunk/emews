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

import emews.base.basenet
import emews.base.config
import emews.base.logger
import emews.base.serv_hub
import emews.base.system_manager
import emews.base.sysprop


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

    node_name = _get_node_name(config_dict_init['general']['node_name'], args.node_name)
    is_hub = True if node_name == config_dict_system['hub']['node_name'] and not args.local \
        else False

    if is_hub or args.local:
        node_id = 1  # hub or local mode node id
    else:
        # The node id is assigned by the hub node.
        # Once node id is assigned, this node will use it whenever connecting to the hub.
        try:
            node_id = _get_node_id(config_dict_system['hub']['node_address'],
                                   config_dict_system['communication']['port'],
                                   config_dict_init['node_init']['hub_timeout'],
                                   config_dict_init['node_init']['hub_max_attempts'])
        except (IOError, KeyboardInterrupt):
            # time to exit
            return None

    emews.base.logger._base_logger = logging.LoggerAdapter(_init_base_logger(
        config_dict_init['logging'], node_id, is_hub=is_hub, is_local=args.local),
        {'nodename': node_name, 'nodeid': node_id})

    sysprop_dict = {
        'node_name': node_name,
        'node_id': node_id,
        'root_path': root_path,
        'is_hub': is_hub,
        'local': args.local
    }

    return emews.base.system_manager.SystemManager(config_dict_system,
                                                   emews.base.sysprop.SysProp(**sysprop_dict))


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


def _get_node_id(addr, port, timeout, max_attempts):
    """Connect to the address given (assuming to be the hub node) to obtain the node id."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    connect_attempts = 0

    while connect_attempts < max_attempts:
        try:
            sock.connect(addr)
            sock.sendall(struct.pack('>HLHL',
                                     emews.base.basenet.NetProto.NET_HUB,
                                     0,  # node id (not assigned yet, so leave at zero)
                                     emews.base.serv_hub.HubProto.HUB_NODE_ID_REQ,
                                     0  # params (none)
                                     ))
            chunk = sock.recv(4)  # node_id (4 bytes)
            node_id = struct.unpack('>L', chunk)
            sock.sendall(struct.pack('>L', node_id))  # ack node id by sending it back
            chunk = sock.recv(2)  # ACK (2 bytes)
            ack = struct.unpack('>H', chunk)
        except (socket.error, struct.error):
            connect_attempts += 1
            continue
        except KeyboardInterrupt:
            # Ctrl-C
            sock.shutdown()
            print "Caught interrupt."
            raise

        if ack == emews.base.basenet.HandlerCB.STATE_ACK_OK:
            sock.shutdown()
            return node_id
        elif ack == emews.base.basenet.HandlerCB.STATE_ACK_NOK:
            # depending on what happened, the node id may be good
            if _check_node_id(addr, port, timeout, max_attempts, node_id):
                sock.shutdown()
                return node_id

    # could not get the node id
    sock.shutdown()
    raise IOError("Could not obtain a node id.")


def _check_node_id(addr, port, timeout, max_attempts, node_id):
    """Check a node id we were given for validity.  Only needed if ACK failed."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    connect_attempts = 0

    while connect_attempts < max_attempts:
        try:
            sock.connect(addr)
            sock.sendall(struct.pack('>HLHL',
                                     emews.base.basenet.NetProto.NET_HUB,
                                     0,  # node id (possibly not assigned yet, so leave at zero)
                                     emews.base.serv_hub.HubProto.HUB_CHECK_NODE_ID,
                                     node_id  # params (potential node id)
                                     ))
            chunk = sock.recv(2)  # ACK (2 bytes)
            ack = struct.unpack('>H', chunk)
        except (socket.error, struct.error):
            connect_attempts += 1
            continue
        except KeyboardInterrupt:
            # Ctrl-C
            sock.shutdown()
            print "Caught interrupt."
            raise

        break

    sock.shutdown()
    if ack == emews.base.basenet.HandlerCB.STATE_ACK_OK:
        return True

    return False


def _init_base_logger(log_config, node_id, is_hub=False, is_local=False):
    """Set up the logger."""
    message_level = log_config['message_level']

    logger = logging.getLogger(log_config['logger_name'])
    logger.setLevel(message_level)
    logger.propagate = False

    if is_local:
        # local mode: log to a stream (stdout)
        stream_path, stream_name = log_config['stream'].rsplit(".", 1)

        handler_obj = logging.StreamHandler(stream=getattr(sys.modules[stream_path], stream_name))
        handler_obj.setLevel(message_level)
        handler_obj.setFormatter(logging.Formatter(log_config['message_format']))
        logger.addHandler(handler_obj)

    elif is_hub:
        # hub node: log to a file
        handler_obj = logging.FileHandler(mode='a', delay=True, filename='emews.log')
        handler_obj.setLevel(message_level)
        handler_obj.setFormatter(logging.Formatter(log_config['message_format']))
        logger.addHandler(handler_obj)

    else:
        # non-hub node: distributed logging
        logger.addHandler(emews.base.logger.DistLogger(node_id))

    return logger
