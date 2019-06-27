"""
SiteCrawler agent environment.

Created on Mar 29, 2019
@author: Brian Ricks
"""
import socket
import struct

import emews.base.timer
import emews.services.base_env


class SiteCrawlerAgentEnv(emews.services.base_env.BaseEnv):
    """Classdocs."""

    __slots__ = ('_cb', '_site_map', '_link_data', '_viral_links', '_viral_link_threshold', '_viral_link_expiration')

    # enums
    LINK_COUNT = 0
    LINK_VIRAL = 1
    LINK_TIMER = 2

    def __init__(self):
        """Constructor."""
        super(SiteCrawlerAgentEnv, self).__init__()

        self._cb = {
            'crawl_site': self._update_crawl_site,
            'link_clicked': self._evidence_viral_link,
        }
        self._site_map = {}  # [node_id]: current site
        self._link_data = {}  # [site]: {[link_index]: link_data}
        self._viral_links = {}  # [site]: list of viral links

        # viral link parameters
        self._viral_link_threshold = 10  # number of specific links clicks, per site, before viral
        self._viral_link_expiration = 60  # seconds that a link remains viral

    def update_evidence(self, new_obs):
        """Produce evidence."""
        cb = self._cb.get(new_obs.key, None)

        if cb is None:
            self.logger.error("%s: observation key '%s' is unknown", self.env_name, new_obs.key)
            raise AttributeError("%s: observation key '%s' is unknown" % (self.env_name, new_obs.key))

        cb(new_obs)

    def _update_crawl_site(self, new_obs):
        """Update site the node is crawling on."""
        self._site_map[new_obs.node_id] = new_obs.value

    def _evidence_viral_link(self, new_obs):
        """Given that the last observation was for this evidence, check for viral link."""
        # New_obs.val is the link index clicked on.  Simply check if enough clicks have occurred.
        # The agent needs to send an observation on what site it is crawling before sending link clicks
        crawl_site = self._env_data['crawl_site'][SiteCrawlerAgentEnv.ENV_DATA_DICT][new_obs.node_id]

        if crawl_site not in self._link_data:
            self._link_data[crawl_site] = {}

        link_data = self._link_data[crawl_site]  # link data is for a specific site

        if new_obs.value not in link_data:
            link_data[new_obs.value] = [0, False, None]  # [link index]: number of clicks, went viral?, viral duration timer

        num_clicks = link_data[new_obs.value][SiteCrawlerAgentEnv.LINK_COUNT] + 1
        link_data[new_obs.value][SiteCrawlerAgentEnv.LINK_COUNT] = num_clicks

        if num_clicks > self._viral_link_threshold and not link_data[new_obs.value][SiteCrawlerAgentEnv.LINK_VIRAL]:
            # viral link, update evidence cache (used for agent ask)
            link_data[new_obs.value][SiteCrawlerAgentEnv.LINK_VIRAL] = True
            if crawl_site not in self._viral
            viral_link_ev = self._evidence_cache[new_obs.node_id].get('viral_link', None)
            if viral_link_ev is None:
                self._evidence_cache[new_obs.node_id]['viral_link'] = []
                viral_link_ev = self._evidence_cache[new_obs.node_id]['viral_link']

            viral_link_ev.append(new_obs.value)

            self.logger.info(
                "%s: link on server '%s' at index '%d' has gone viral",
                self.env_name, socket.inet_ntoa(struct.pack(">I", crawl_site)), new_obs.value)
            self._thread_dispatcher.dispatch(
                emews.base.timer.Timer(
                    env_data[SiteCrawlerAgentEnv.ENV_DATA_EXP], self._evidence_viral_link_expired, [new_obs.node_id, crawl_site, new_obs.value]))

    def _evidence_viral_link_expired(self, node_id, crawl_site, link_index):
        """When a timer has finished, this will be invoked."""
        viral_link_ev = self._evidence_cache[node_id]['viral_link']
        viral_link_ev.remove(link_index)

        if not len(viral_link_ev):
            # remove the evidence key as it no longer has any values
            del self._evidence_cache[node_id]['viral_link']

        self.logger.info(
            "%s: link on server '%s' at index '%d' is no longer viral",
            self.env_name, socket.inet_ntoa(struct.pack(">I", crawl_site)), link_index)
