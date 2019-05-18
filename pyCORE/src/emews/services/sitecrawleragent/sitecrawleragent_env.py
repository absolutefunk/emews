"""
SiteCrawler agent environment.

Created on Mar 29, 2019
@author: Brian Ricks
"""

import emews.services.base_env


class SiteCrawlerEnv(emews.services.base_env.BaseEnv):
    """Classdocs."""

    __slots__ = ()

    def __init__(self):
        """Constructor."""
        super(SiteCrawlerEnv, self).__init__()

    def update_evidence(self, new_obs):
        """Produce evidence."""
