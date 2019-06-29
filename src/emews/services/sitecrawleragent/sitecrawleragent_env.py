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
        """@Override Produce evidence."""
        cb = self._cb.get(new_obs.key, None)

        if cb is None:
            self.logger.error("%s: observation key '%s' is unknown", self.env_name, new_obs.key)
            raise AttributeError("%s: observation key '%s' is unknown" % (self.env_name, new_obs.key))

        cb(new_obs)

    def get_evidence_list(self, node_id, key):
        """@Override Return the relevant list of evidence given the key and a node id."""
        crawl_site = self._site_map.get(node_id, None)
        if crawl_site is None:
            return []

        viral_links = self._viral_links.get(crawl_site, None)
        if viral_links is None:
            return []

        return viral_links

    def _update_crawl_site(self, new_obs):
        """Update site the node is crawling on."""
        self._site_map[new_obs.node_id] = new_obs.value

    def _evidence_viral_link(self, new_obs):
        """Given that the last observation was for this evidence, check for viral link."""
        # New_obs.val is the link index clicked on.  Simply check if enough clicks have occurred.
        # The agent needs to send an observation on what site it is crawling before sending link clicks
        crawl_site = self._site_map[new_obs.node_id]

        if crawl_site not in self._link_data:
            self._link_data[crawl_site] = {}

        link_data = self._link_data[crawl_site]  # link data is for a specific site

        if new_obs.value not in link_data:
            link_data[new_obs.value] = [0, False, None]  # [link index]: number of clicks, went viral?, viral duration timer

        num_clicks = link_data[new_obs.value][SiteCrawlerAgentEnv.LINK_COUNT] + 1
        link_data[new_obs.value][SiteCrawlerAgentEnv.LINK_COUNT] = num_clicks

        if num_clicks > self._viral_link_threshold and not link_data[new_obs.value][SiteCrawlerAgentEnv.LINK_VIRAL]:
            # viral link, update evidence (used for agent ask)
            link_data[new_obs.value][SiteCrawlerAgentEnv.LINK_VIRAL] = True
            if crawl_site not in self._viral_links:
                self._viral_links[crawl_site] = []

            self._viral_links[crawl_site].append(new_obs.value)

            self.logger.info(
                "%s: link on server '%s' at index '%d' has gone viral",
                self.env_name, socket.inet_ntoa(struct.pack(">I", crawl_site)), new_obs.value)
            self._thread_dispatcher.dispatch(
                emews.base.timer.Timer(
                    self._viral_link_expiration, self._evidence_viral_link_expired, [new_obs.node_id, crawl_site, new_obs.value]))

    def _evidence_viral_link_expired(self, node_id, crawl_site, link_index):
        """When a timer has finished, this will be invoked."""
        self._viral_links[crawl_site].remove(link_index)

        self.logger.info(
            "%s: link on server '%s' at index '%d' is no longer viral",
            self.env_name, socket.inet_ntoa(struct.pack(">I", crawl_site)), link_index)
