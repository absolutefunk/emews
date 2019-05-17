"""
Base class for service agent environments.

Concrete environment classes are located in the service folder of their respective service agents,
and end with '_env'.  Environment classes provide the logic necessary for state updates based on
agent observations.

Created on Mar 29, 2019
@author: Brian Ricks
"""
from abc import abstractmethod
import time

import emews.base.baseobject


class Observation(object):
    """observation params."""

    MSG_RO = "Observation attributes are read-only."

    __slots__ = ('timestamp',
                 'node_id',
                 'value')

    def __init__(self, **kwargs):
        """Constructor."""
        for attr, value in kwargs.iteritems():
            object.__setattr__(self, attr, value)

    def __setattr__(self, attr, value):
        """Attributes are not mutable."""
        raise AttributeError(Observation.MSG_RO)


class BaseEnv(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_env_id', '_obs_cache', '_ev_cache')

    def __init__(self):
        """Constructor."""
        self._obs_cache = {}  # [obs_key]: list of observations (ordered by time)
        self._ev_cache = {}  # [ev_key]: ev_val

    @property
    def env_id(self):
        """Return the env id."""
        return self._env_id

    def get_evidence(self, ev_key):
        """Given an evidence key, return the evidence."""


    def put_observation(self, node_id, obs_key, obs_val):
        """Given an observation key and value, update the observation."""
        new_obs = Observation(timestamp=time.time(), node_id=node_id, value=obs_val)


    @abstractmethod
    def update_evidence(self):
        """Produce evidence."""
        pass
