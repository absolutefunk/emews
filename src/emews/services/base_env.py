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
                 'key',
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

    __slots__ = ('env_name', '_env_id', '_thread_dispatcher')

    def __init__(self):
        """Constructor."""
        super(BaseEnv, self).__init__()

    @property
    def env_id(self):
        """Return the env id."""
        return self._env_id

    def get_evidence(self, node_id, key):
        """Return the current evidence by key."""
        ev_list = self.get_evidence_list(node_id, key)
        if not len(ev_list):
            return '0'

        ev_str = ''
        for val in ev_list:
            ev_str += str(val) + ","
        ev_str = ev_str[:-1] + " "  # remove last comma

        return ev_str[:-1]  # last character is a space

    def put_observation(self, node_id, obs_key, obs_val):
        """Given an observation key and value, update the observation."""
        self.logger.debug("%s: new observation from node %d '%s', %d",
                          self.env_name, node_id, obs_key, obs_val)

        new_obs = Observation(timestamp=time.time(), node_id=node_id, key=obs_key, value=obs_val)

        self.update_evidence(new_obs)

    @abstractmethod
    def get_evidence_list(self, node_id, key):
        """Return the relevant list of evidence given the key and a node id."""
        pass

    @abstractmethod
    def update_evidence(self, new_obs):
        """Produce evidence."""
        pass
