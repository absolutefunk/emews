"""
eMews web site crawler service.

Created on Jan 19, 2018
@author: Brian Ricks
"""
import ssl

import mechanize

import emews.services.baseagent


class SiteCrawlerAgent(emews.services.baseagent.BaseAgent):
    """Classdocs."""

    __slots__ = ('_br',
                 '_invalid_link_prefixes',
                 '_siteURLs',
                 '_std_deviation_link',
                 '_site_sampler',
                 '_num_links_sampler',
                 '_link_viral_odds',
                 '_link_delay_sampler')

    def __init__(self, config):
        """Constructor."""
        super(SiteCrawlerAgent, self).__init__()

        self._br = mechanize.Browser()
        # no, I am not a robot ;-)
        self._br.set_handle_robots(False)

        self._invalid_link_prefixes = config['invalid_link_prefixes']  # list
        self._siteURLs = config['start_sites']  # list

        self._site_sampler = self.sys.import_component(config['site_sampler'])
        self._num_links_sampler = self.sys.import_component(config['num_links_sampler'])
        self._link_delay_sampler = self.sys.import_component(config['link_delay_sampler'])

        self._link_viral_odds = config['link_viral_odds']

        # set user agent string to something real-world
        self._br.addheaders = [('User-agent', config['user_agent'])]

    def _get_next_link_index(self, page_links, std_deviation=None):
        """Given a list of page links, find and return the index of the first valid link."""
        if not page_links:
            self.logger.debug("Crawled page doesn't have any links to further crawl.")
            return None
        elif len(page_links) == 1:
            if self._checklink(page_links[0]):
                selected_link_index = 0
            else:
                return None

        while len(page_links) > 1:
            # keep looping until a valid link is found
            # sample the next link
            ev_viral_links = self.ask().get('viral_link', [])

            current_evidence = ''
            for v_link in ev_viral_links:
                current_evidence += str(v_link) + ","
            self.logger.debug("Current evidence: %s", current_evidence)

            selected_link_index = self._inference(ev_viral_links)

            if self._checklink(page_links[selected_link_index]):
                break

            # strip the bad link from the list and try again
            del page_links[selected_link_index]

        if not page_links:
            self.logger.debug("Crawled page doesn't have any (valid) links to further crawl.")
            return None

        self.tell('link_clicked', selected_link_index)

        return selected_link_index

    def _inference(self, viral_links):
        """Perform inference on the factored joint."""
        return 0

    def _checklink(self, link_str):
        """Check a link object's URL for validity (not a javascript link or something)."""
        for prefix in self._invalid_link_prefixes:
            if link_str.absolute_url.lower().startswith(prefix):
                return False

        return True

    def run_service(self):
        """Crawl a web site, starting from the _siteURL, picking links from each page visited."""
        # Disable SSL cert verification, as most likely we will be using self-signed certs (HTTPS)
        # https://stackoverflow.com/questions/30551400/disable-ssl-certificate-validation-in-mechanize
        # TODO: clean this up (maybe add a config option to enable SSL no-check-cert, or autodetect)
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            # Legacy Python that doesn't verify HTTPS certificates by default
            pass
        else:
            # Handle target environment that doesn't support HTTPS verification
            ssl._create_default_https_context = _create_unverified_https_context

        site_url = self._siteURLs[self._site_sampler.sample()]
        try:
            self._br.open(site_url)
        except Exception as ex:
            self.logger.warning("On site open: %s, (server: %s)", ex, site_url)
            return
        # Forces output to be considered HTML (output usually is).
        self._br._factory.is_html = True  # pylint: disable=W0212
        self.logger.info("HTTP server up, starting crawl at %s ...", site_url)

        # Setup the total number of links to crawl.  As a heuristic, it uses the number of links
        # from the first page as an upper bound.
        self._num_links_sampler.update(upper_bound=len(list(self._br.links())))
        num_links_to_crawl = self._num_links_sampler.sample()

        # now crawl for (max) num_links_to_crawl
        for _ in range(num_links_to_crawl):
            if self.interrupted:
                break

            page_links = list(self._br.links())
            selected_link_index = self._get_next_link_index(page_links)
            if selected_link_index is None:
                break

            next_link = page_links[selected_link_index]
            self.sleep(self._link_delay_sampler.sample())
            # we need to check if the end of sleep was due to being interrupted
            if self.interrupted:
                break

            self.logger.debug("link index (%d/%d): %s", selected_link_index, len(page_links),
                              next_link.absolute_url)

            try:
                self._br.follow_link(link=next_link)
            except Exception as ex:
                self.logger.warning("On follow_link: %s, (server: %s)", ex, site_url)
                break

        self.logger.info("Finished crawl at %s ...", site_url)
