"""
Hub server.

Handles core hub related communication.

Created on Apr 9, 2019
@author: Brian Ricks
"""
import struct

import emews.base.baseserv


class NodeCache(object):
    """Container for caching what the hub currently knows about other nodes."""

    # Enums
    CACHE_SIZE = 3  # number of dicts in the cache

    INDEX_NAME_ID = 0
    INDEX_ID_NAME = 1
    INDEX_NAME_ADDR = 2

    __slots__ = ('_node_cache', '_cache_miss_cb')

    def __init__(self):
        """Constructor."""
        self._node_cache = [None] * self.CACHE_SIZE
        self._cache_miss_cb = [None] * self.CACHE_SIZE

        self._node_cache.insert(self.INDEX_NAME_ADDR, {})
        self._cache_miss_cb.insert(self.INDEX_NAME_ADDR, None)  # TODO: put cb method here

    def get(self, index, key):
        """
        Return value at key in dict at index.

        If key missing, fill in k/v.
        """
        try:
            val = self._node_cache[index][key]
        except KeyError:
            # cache miss
            val = self._cache_miss_cb[index](key)
            self._node_cache[index][key] = val

        return val

    def add(self, index, key, val):
        """Add the k/v at index."""
        self._node_cache[index][key] = val


class ServHub(emews.base.baseserv):
    """Classdocs."""

    __slots__ = ('_cb')

    def __init__(self):
        """Constructor."""
        self._cb = []
        self._cb.append(None)  # Index [0]

    def serv_init(self, id, node_id, service_id):
        """Init of new node-hub session.  Next expected chunk is request from node."""
        return (self._hub_query, 4)

    def _hub_query(self, id, chunk):
