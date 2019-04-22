"""
Enumerations and constants.

Created on Apr 17, 2019
@author: Brian Ricks
"""


class net_protocols(object):
    """Enumerations for supported protocols."""

    __slots__ = ()

    ENUM_SIZE = 7

    NET_NONE = 0       # placeholder
    NET_CC_1 = 1       # CC channel (future)
    NET_CC_2 = 2       # CC channel (future)
    NET_LOGGING = 3    # distributed logging
    NET_AGENT = 4      # agent-based communication
    NET_HUB = 5        # hub-based communication
    NET_SPAWN = 6      # service spwaning


class hub_protocols(object):
    """Enumerations for supported hub requests."""

    __slots__ = ()

    ENUM_SIZE = 3

    HUB_NONE = 0            # placeholder
    HUB_NODE_ID_REQ = 1     # request a global node id
    HUB_SERVICE_ID_REQ = 2  # request a global service id


class spawner_protocols(object):
    """Enumerations for supported spawner requests."""

    __slots__ = ()

    ENUM_SIZE = 2

    SPAWNER_NONE = 0            # placeholder
    SPAWNER_LAUNCH_SERVICE = 1  # launch (spawn) a service


class net_state(object):
    """Constants for different net states."""

    __slots__ = ()

    STATE_ACK = 17
    STATE_NACK = 19
