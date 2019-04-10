"""
Base class for service agent environments.

Concrete environment classes are located in the service folder of their respective service agents,
and end with '_env'.

Created on Mar 29, 2019
@author: Brian Ricks
"""
from abc import abstractmethod

import emews.services.baseservice


class BaseEnv(emews.services.baseservice.BaseService):
    """Classdocs."""

    __slots__ = ()

    def __init__(self):
        """Constructor."""
        super(BaseEnv, self).__init__()

    @abstractmethod
    def tell(self, context, state):
        """
        Tell eMews about a state change (ie, a new state) at some given context.

        Tell is the analogue to ask, which agents use to query the environment.
        """
        pass
