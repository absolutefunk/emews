"""
Base class for service agent environments.

Concrete environment classes are located in the service folder of their respective service agents,
and end with '_env'.  Environment classes provide the logic necessary for state updates based on
agent observations.

Created on Mar 29, 2019
@author: Brian Ricks
"""
from abc import abstractmethod

import emews.base.baseobject


class BaseEnv(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_env_id')

    @property
    def env_id(self):
        """Return the env id."""
        return self._env_id

    @abstractmethod
    def get_evidence(self, ev_key):
        """Given an evidence key, return the evidence."""
        pass

    @abstractmethod
    def update_observation(self, obs_key, obs_val):
        """Given an observation key and value, update the observation."""
        pass
