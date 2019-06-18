"""
eMews web site crawler service.

Created on Jan 19, 2018
@author: Brian Ricks
"""
import ssl

import mechanize

import emews.services.baseservice


class SiteCrawler(emews.services.baseservice.BaseService):
    """Classdocs."""

    __slots__ = ('_invalid_link_prefixes',
                 '_siteURLs',
                 '_std_deviation_link',
                 '_site_sampler',
                 '_num_links_sampler',
                 '_link_sampler',
                 '_link_delay_sampler',
                 '_br_header')

    def __init__(self, config):
        """Constructor."""
        super(SiteCrawler, self).__init__()

        self._invalid_link_prefixes = config['invalid_link_prefixes']  # list
        self._siteURLs = config['start_sites']  # list

        self._std_deviation_link = config['link_sampler_sigma_next']

        self._site_sampler = self.sys.import_component(config['site_sampler'])
        self._num_links_sampler = self.sys.import_component(config['num_links_sampler'])
        self._link_sampler = self.sys.import_component(config['link_sampler'])
        self._link_delay_sampler = self.sys.import_component(config['link_delay_sampler'])

        # set user agent string to something real-world
        self._br_header = config['user_agent']

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
            # parameters updated here as removing links will change our upper_bound
            if std_deviation is None:
                self._link_sampler.update(upper_bound=len(page_links) - 1)
            else:
                self._link_sampler.update(upper_bound=len(page_links) - 1, sigma=std_deviation)

            selected_link_index = self._link_sampler.sample()

            if self._checklink(page_links[selected_link_index]):
                break

            # strip the bad link from the list and try again
            del page_links[selected_link_index]

        if not page_links:
            self.logger.debug("Crawled page doesn't have any (valid) links to further crawl.")
            return None

        return selected_link_index

    def _checklink(self, link_str):
        """Check a link object's URL for validity (not a javascript link or something)."""
        for prefix in self._invalid_link_prefixes:
            if link_str.absolute_url.lower().startswith(prefix):
                return False

        return True

    def run_service(self):
        """Crawl a web site, starting from the _siteURL, picking links from each page visited."""
        br = mechanize.Browser()
        # no, I am not a robot ;-)
        br.set_handle_robots(False)
        br.addheaders = [('User-agent', self._br_header)]

        site_url = self._siteURLs[self._site_sampler.sample()]
        try:
            br.open(site_url)
        except Exception as ex:
            self.logger.warning("On site open: %s, (server: %s)", ex, site_url)
            return

        # Forces output to be considered HTML (output usually is).
        br._factory.is_html = True  # pylint: disable=W0212
        self.logger.info("HTTP server up, starting crawl at %s ...", site_url)

        # Crawl to the first link.  This will allow us to set the link delay parameters correctly.
        page_links = list(br.links())
        selected_link_index = self._get_next_link_index(page_links)
        if selected_link_index is None:
            return

        next_link = page_links[selected_link_index]  # get next link from list
        self.sleep(self._link_delay_sampler.sample())  # wait a random amount of time
        # we need to check if the end of sleep was due to being interrupted
        if self.interrupted:
            return

        try:
            br.follow_link(link=next_link)  # crawl to next link
        except Exception as ex:
            self.logger.warning("On follow_link: %s, (server: %s)", ex, site_url)
            return

        self.logger.debug("selected link index (%d/%d): selected page: %s", selected_link_index,
                          len(page_links), next_link.absolute_url)

        # Setup the total number of links to crawl.  As a heuristic, it uses the index of the
        # first link selected as the upper bound and selects a total crawl length based on this
        # index.
        # TODO: the heuristic presents a subtle bug if the selected index is zero, given that the
        # lower bound on the sampler is also zero.  Currently just using the page link count, which
        # works well for index pages of small link count.
        self._num_links_sampler.update(upper_bound=len(page_links))
        num_links_to_crawl = self._num_links_sampler.sample()

        # now crawl for (max) num_links_to_crawl
        for _ in range(num_links_to_crawl):
            if self.interrupted:
                break

            page_links = list(br.links())
            # use the std_deviation for > first iteration from now on
            selected_link_index = self._get_next_link_index(page_links, std_deviation=self._std_deviation_link)
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
                br.follow_link(link=next_link)
            except Exception as ex:
                self.logger.warning("On follow_link: %s, (server: %s)", ex, site_url)
                break

        self.logger.info("Finished crawl at %s ...", site_url)
