"""
SiteCrawler agent environment.

Created on Mar 29, 2019
@author: Brian Ricks
"""

import emews.base.timer
import emews.services.base_env


class SiteCrawlerEnv(emews.services.base_env.BaseEnv):
    """Classdocs."""

    __slots__ = ('_ev_data')

    # enums
    EV_DATA_CB = 0
    EV_DATA_LINK = 1
    EV_DATA_THRESH = 2
    EV_DATA_EXP = 3
    LINK_COUNT = 0
    LINK_VIRAL = 1
    LINK_TIMER = 2

    def __init__(self):
        """Constructor."""
        super(SiteCrawlerEnv, self).__init__()

        self._ev_data = {}
        self._ev_data['viral_link'] = [self._evidence_viral_link, {}, 20, 60]  # callback, link data, viral threshold, expiration

    def update_evidence(self, new_obs):
        """Produce evidence."""
        ev_data = self._ev_data.get(new_obs.key, None)

        if ev_data is None:
            self.logger.error("%s: observation key '%s' is unknown", self.env_name, new_obs.key)
            raise AttributeError("%s: observation key '%s' is unknown", self.env_name, new_obs.key)

        ev_data[SiteCrawlerEnv.EV_DATA_CB](new_obs)

    def _evidence_viral_link(self, new_obs):
        """Given that the last observation was for this evidence, check for viral link."""
        # New_obs.val is the link index clicked on.  Simply check if enough clicks have occurred.
        ev_data = self._ev_data['viral_link']
        link_data = ev_data[SiteCrawlerEnv.EV_DATA_LINK]

        if new_obs.value not in link_data:
            link_data[new_obs.value] = [0, False, None]  # [link index]: number of clicks, went viral?, viral duration timer

        num_clicks = link_data[new_obs.value][SiteCrawlerEnv.LINK_COUNT] + 1
        link_data[new_obs.value][SiteCrawlerEnv.LINK_COUNT] = num_clicks

        if num_clicks > ev_data[SiteCrawlerEnv.EV_DATA_THRESH] and not link_data[new_obs.value][SiteCrawlerEnv.LINK_VIRAL]:
            # viral link
            self.logger.info("%s: link at index '%d' has gone viral", self.env_name, new_obs.value)
            self._thread_dispatcher.dispatch(
                emews.base.timer.Timer(
                    ev_data[SiteCrawlerEnv.EV_DATA_EXP]), self._evidence_viral_link_expired, [new_obs.value])

    def _evidence_viral_link_expired(self, link_index):
        """When a timer has finished, this will be invoked."""
        self._ev_data['viral_link'][SiteCrawlerEnv.EV_DATA_LINK][link_index][SiteCrawlerEnv.LINK_VIRAL] = True
        self.logger.info("%s: link at index '%d' is no longer viral", self.env_name, link_index)
