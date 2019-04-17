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

    if is_hub or args.local:
        node_id = 1  # hub or local mode node id
    else:
        # The node id is assigned by the hub node.
        # Once node id is assigned, this node will use it whenever connecting to the hub.
        try:
            if config_dict_system['hub']['node_address'] is None:
                # hub address is provided to us
                hub_addr = _listen_hub(config_dict_system['communication']['port'],
                                       config_dict_init['communication']['hub_broadcast_wait'],
                                       config_dict_init['communication']['hub_broadcast_max_attempts'],
                                       config_dict_init['general']['node_name_length'],
                                       config_dict_system['hub']['node_name'])
            else:
                hub_addr = config_dict_system['hub']['node_address']

            node_id = _get_node_id(hub_addr,
                                   config_dict_system['communication']['port'],
                                   config_dict_system['communication']['connect_timeout'],
                                   config_dict_system['communication']['connect_max_attempts'])
        except (IOError, KeyboardInterrupt):
            # time to exit
            return None

    print "[system_init] Node id: " + str(node_id) + "."

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
    sock.bind(('', port))
    sock.settimeout(timeout)
    recv_attempts = 0

    while recv_attempts < max_attempts:
        print "[system_init] Listening for broadcast from hub node (attempt " + \
            str(recv_attempts + 1) + "\\" + str(max_attempts) + ", timeout per attempt: " + \
            str(timeout) + "s) ..."
        try:
            (addr, chunk) = sock.recvfrom(buf_size)

            if chunk != hub_name:
                recv_attempts += 1
                continue

        except socket.error:
            recv_attempts += 1
            continue
        except KeyboardInterrupt:
            print "Caught interrupt ..."
            sock.close()
            raise

        break

    sock.close()
    if recv_attempts == max_attempts:
        # could not recv a broadcast from the hub node
        print "[system_init] Did not receive broadcast from hub node."
        raise IOError("Did not receive broadcast from hub node.")

    return addr


def _get_node_id(addr, port, timeout, max_attempts):
    """Connect to the address given (assuming to be the hub node) to obtain the node id."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    connect_attempts = 0

    while connect_attempts < max_attempts:
        print "[system_init] Attempting to obtain node id from hub node (attempt " + \
            str(connect_attempts + 1) + "\\" + str(max_attempts) + ", timeout per attempt: " + \
            str(timeout) + "s) ..."
        try:
            sock.connect((addr, port))
            sock.sendall(struct.pack('>HLHL',
                                     emews.base.basenet.NetProto.NET_HUB,
                                     0,  # node id (not assigned yet, so leave at zero),
                                     emews.base.serv_hub.HubProto.HUB_NODE_ID_REQ,
                                     0  # params (none)
                                     ))
            chunk = sock.recv(4)  # node_id (4 bytes)
            node_id = struct.unpack('>L', chunk)
        except (socket.error, struct.error):
            connect_attempts += 1
            continue
        except KeyboardInterrupt:
            print "Caught interrupt ..."

            try:
                # this may fail if socket endpoint is already closed
                sock.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass

            sock.close()
            raise

        break

    try:
        # this most likely will fail as the hub node should have closed the connection
        sock.shutdown(socket.SHUT_RDWR)
    except socket.error:
        pass

    sock.close()

    if connect_attempts == max_attempts:
        # could not get the node id
        print "[system_init] Could not obtain a node id from hub node."
        raise IOError("Could not obtain a node id from hub node.")

    return node_id


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
