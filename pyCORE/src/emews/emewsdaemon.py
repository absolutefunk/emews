"""
Driver for running eMews services and other components.

Because each node in an emulation environment is assumed to be contained (ie,
each node has its own process space and network stack), the daemon would need
to be spawned once per node.  Once the daemon process is started, eMews services
are spawned as threads.  This way the resource footprint is minimized per node,
as in addition to the resources saved by having one process for all services,
other aspects (such as logging and control of services) is shared among all
service threads.

Created on Mar 24, 2018
@author: Brian Ricks
"""
import argparse

import emews.base.system_init
import emews.version

# TODO: test launching eMews with python -OO


def main():
    """Bootstrap eMews daemon."""
    parser = argparse.ArgumentParser(description='eMews network node daemon')
    parser.add_argument("-s", "--sys_config", help="path of the eMews system config file "
                        "(default: eMews root)")
    parser.add_argument("-c", "--node_config", help="path of the eMews node-based config file "
                        "(default: <none>)")
    parser.add_argument("-n", "--node_name", help="name of the node this daemon launches under "
                        "(default: system host name, if --node_config not given)")
    # TODO: Implement local mode.  May subsume the standalone launcher...
    parser.add_argument("-l", "--local", action='store_true', help="launches the eMews daemon in "
                        "local mode")
    args = parser.parse_args()

    print "eMews %s" % emews.version.__version__

    system_manager = emews.base.system_init.system_init(args)
    system_manager.start()

    print "eMews shutdown"


if __name__ == '__main__':
    main()
