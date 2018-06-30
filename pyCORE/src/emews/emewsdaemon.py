'''
Driver for running emews services and other components.

Because each node in an emulation environment is assumed to be contained (ie,
each node has its own process space and network stack), the daemon would need
to be spawned once per node.  Once the daemon process is started, emews services
are spawned as threads.  This way the resource footprint is minimized per node,
as in addition to the resources saved by having one process for all services,
other aspects (such as logging and control of services) is shared among all
service threads.

Created on Mar 24, 2018
@author: Brian Ricks
'''
import argparse

def launch_logserver(config):
    '''
    Determines if the LogServer should be launched.  Criteria for this to occur:
    - Logging base_logger is configured as 'emews.distributed'
    - This node is the designated LogServer node.
    '''
    # TODO: All this is obsolete, remove...
    try:
        if config.get_sys('logging', 'main_logger') != 'emews.distributed':
            # not using distributed logging
            return None
    except KeychainException as ex:
        print "A required key in the system config file is missing."
        print ex
        sys.exit(1)

    try:
        logserver_node = config.get_sys('logserver', 'node')
    except KeychainException as ex:
        print "A required key in the system config file is missing."
        print ex
        sys.exit(1)

    if config.nodename == logserver_node:
        # launch the log server
        print "  This node is configured to receive distributed log entries."
        return emews.base.threadwrapper.ThreadWrapper(
            emews.services.logserver.logserver.LogServer(config))

    return None

def main():
    '''
    main function
    '''
    parser = argparse.ArgumentParser(description='eMews network node daemon')
    parser.add_argument("-s", "--sys_config", help="path of the eMews system config file "\
    "(default: eMews root)")
    parser.add_argument("-c", "--node_config", help="path of the eMews node-based config file "\
    "(default: <none>)")
    parser.add_argument("-n", "--node_name", help="name of the node this daemon launches under "\
    "(default: system host name, if --node_config not given)")
    parser.add_argument("-l", "--local", help="launches the eMews daemon in local mode")
    args = parser.parse_args()

    sys_config_path = os.path.join(os.path.dirname(emews.version.__file__), "system.yml")\
        if args.sys_config is None else args.sys_config

    print "eMews %s" % emews.version.__version__
    print "  Using system config path: " + sys_config_path

    config = emews.base.config.Config(sys_config_path,
                                      node_config_path=args.node_config,
                                      node_name=args.node_name)

    print "  Using node name: " + config.nodename

    # When disabling, log messages are cached until logging is enabled again
    logging.disable(logging.CRITICAL)  # disable all log levels
    log_server = launch_logserver(config)
    logging.disable(logging.NOTSET)  # enable all log levels

    try:
        connection_manager = ConnectionManager(config)
        connection_manager.start()
    except StandardError:
        # shutdown LogServer if it is running
        if log_server is not None:
            log_server.stop()
        raise

    if log_server is not None:
        log_server.stop()
        log_shutdown_delay = config.get_sys('logserver', 'shutdown_wait')
        if log_shutdown_delay < 0:
            log_shutdown_delay = None
        log_server.join(log_shutdown_delay)

    print "eMews shutdown"

if __name__ == '__main__':
    main()
