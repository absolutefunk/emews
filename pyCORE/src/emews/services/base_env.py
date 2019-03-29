"""
Base class for service agent environments.

Concrete environment classes are located in the service folder of their respective service agents,
and end with '_env'.

Created on Mar 29, 2019
@author: Brian Ricks
"""

import emews.services.baseservice


class BaseEnv(emews.services.baseservice.BaseService):
    """Classdocs."""

    __slots__ = ()

    def __init__(self):
        """Constructor."""
        super(BaseEnv, self).__init__()
