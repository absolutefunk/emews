"""
eMews web site crawler service.

Created on Jan 19, 2018
@author: Brian Ricks
"""
import math
import random
import ssl
import socket
import struct

import mechanize

import emews.services.baseagent


class AgentModel(object):
    """Next link sampler."""

    __slots__ = ('prior', 'ev_viral', 'ev_visited', 'num_pref_links')

    def __init__(self):
        """Constructor."""
        self.prior = [None] * 2  # class variable
        self.ev_viral = [None] * 2  # attribute variables
        self.ev_visited = [None] * 2
        self.num_pref_links = 0

    def set_prior_param(self, num_links, links_preferred, links_preferred_strength):
        """Set the prior."""
        self.num_pref_links = 0
        for index in links_preferred:
            if index >= 0 and index < num_links:
                self.num_pref_links += 1

        norm = ((self.num_pref_links * links_preferred_strength) + num_links - self.num_pref_links) / float(num_links)

        self.prior[0] = links_preferred_strength / (num_links * norm)
        self.prior[1] = 1.0 / (num_links * norm)

    def set_evidence_params(self, link_viral_strength, link_visited_strength, num_links):
        """Set the evidence variable parameters."""
        norm = (link_viral_strength + num_links - 1.0) / float(num_links)
        self.ev_viral[0] = link_viral_strength / (num_links * norm)
        self.ev_viral[1] = 1.0 / (num_links * norm)

        norm = (link_visited_strength + num_links - 1.0) / float(num_links)
        self.ev_visited[0] = link_visited_strength / (num_links * norm)
        self.ev_visited[1] = 1.0 / (num_links * norm)


class SiteCrawlerAgent(emews.services.baseagent.BaseAgent):
    """Classdocs."""

    __slots__ = ('_invalid_link_prefixes',
                 '_siteURLs',
                 '_std_deviation_link',
                 '_site_sampler',
                 '_num_links_sampler',
                 '_link_viral_strength',
                 '_link_visited_strength',
                 '_link_delay_sampler',
                 '_next_link_model',
                 '_visited_links',
                 '_links_preferred',
                 '_links_preferred_strength',
                 '_br_header')

    def __init__(self, config):
        """Constructor."""
        super(SiteCrawlerAgent, self).__init__()

        self._invalid_link_prefixes = config['invalid_link_prefixes']  # list
        self._siteURLs = config['start_sites']  # list

        self._site_sampler = self.sys.import_component(config['site_sampler'])
        self._num_links_sampler = self.sys.import_component(config['num_links_sampler'])
        self._link_delay_sampler = self.sys.import_component(config['link_delay_sampler'])

        self._link_viral_strength = config['link_viral_strength']
        self._link_visited_strength = config['link_visited_strength']
        self._next_link_model = AgentModel()
        self._visited_links = set()  # local evidence

        self._links_preferred = config['links_preferred']  # list
        self._links_preferred_strength = config['links_preferred_strength']

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
            # sample the next link
            self._update_model(len(page_links))
            ev_viral_links = self.ask().get('viral_link', [])

            current_evidence = ''
            for v_link in ev_viral_links:
                current_evidence += str(v_link) + ","
            self.logger.debug("Current evidence: %s", current_evidence)

            selected_link_index = self._sample(ev_viral_links, len(page_links))

            if self._checklink(page_links[selected_link_index]):
                break

            # strip the bad link from the list and try again
            del page_links[selected_link_index]

        if not page_links:
            self.logger.debug("Crawled page doesn't have any (valid) links to further crawl.")
            return None

        self.tell('link_clicked', selected_link_index)
        self._visited_links.add(selected_link_index)

        return selected_link_index

    def _update_model(self, num_links):
        """Build the model based on the number of links.  Evidence count is consistent."""
        # rebuild prior (class) distribution
        self._next_link_model.set_prior_param(num_links, self._links_preferred, self._links_preferred_strength)
        # rebuild conditional distributions
        self._next_link_model.set_evidence_params(
            self._link_viral_strength, self._link_visited_strength, num_links)
        self.logger.debug(
            "Agent Model: attributes (prior): pref=%f, not_pref=%f (state_space=2, num_attributes=%d, num_pref_links=%d)",
            self._next_link_model.prior[0], self._next_link_model.prior[1], num_links, self._next_link_model.num_pref_links)
        self.logger.debug(
            "Agent Model: attributes (evidence): viral=%f, not_viral=%f (state_space=2, num_attributes=%d)",
            self._next_link_model.ev_viral[0], self._next_link_model.ev_viral[1], num_links)
        self.logger.debug(
            "Agent Model: attributes (evidence): visited=%f, not_visited=%f (state_space=2, num_attributes=%d)",
            self._next_link_model.ev_visited[0], self._next_link_model.ev_visited[1], num_links)

    def _prob_to_log(self, prob):
        """Convert a probability to a log prob."""
        if prob > 0.0:
            return math.log(prob)  # base e

        return -28.0  # represent an arbitarily small probability

    def _sample(self, viral_links, num_links):
        """Perform inference on the factored joint, and sample."""
        log_prior_pref = self._prob_to_log(self._next_link_model.prior[0])
        log_prior_nonpref = self._prob_to_log(self._next_link_model.prior[1])
        log_viral = self._prob_to_log(self._next_link_model.ev_viral[0])
        log_nonviral = self._prob_to_log(self._next_link_model.ev_viral[1])
        log_visited = self._prob_to_log(self._next_link_model.ev_visited[0])
        log_nonvisited = self._prob_to_log(self._next_link_model.ev_visited[1])

        posteriors = []
        # init to appropriate prior
        for i in xrange(num_links):
            if i in self._links_preferred:
                posteriors.append(log_prior_pref)
            else:
                posteriors.append(log_prior_nonpref)

        for i in xrange(num_links):
            # for each link in prior (links to click)
            nonviral_count = num_links
            nonvisited_count = num_links
            if i in viral_links:
                # if the link at index i is viral, append viral prob for evidence node i
                # Note that we only do this once per index i, even if multiple videos are viral.
                # This is a consequence of the naive Bayes assumption.
                posteriors[i] += log_viral
                nonviral_count -= 1  # the link at index i is viral, so decrement
            if i in self._visited_links:
                posteriors[i] += log_visited
                nonvisited_count -= 1

            posteriors[i] += nonviral_count * log_nonviral
            posteriors[i] += nonvisited_count * log_nonvisited

        # find the normalization constant, P(e).  Because we are in log space we gotta be sneaky.
        # step 1, find the smallest log and pre-normalize the others with it.
        smallest_post = 0.0
        for posterior in posteriors:
            if posterior < smallest_post:
                smallest_post = posterior

        # step 2, pre-normalize by largest_neg_post, and exponentiate
        for i in xrange(len(posteriors)):
            posteriors[i] -= smallest_post
            if posteriors[i] < -21:
                # anything smaller than this may cause underflow issues, treat as exp(zero) = 1
                posteriors[i] = 1.0
            else:
                posteriors[i] = math.exp(posteriors[i])

        norm = 0.0
        for posterior in posteriors:
            norm += posterior
        norm = 1.0 / norm

        for i in xrange(len(posteriors)):
            posteriors[i] = posteriors[i] * norm
            # self.logger.debug("POSTERIOR: %f", posteriors[i])

        # sample from the posterior
        r_sample = random.random()  # [0.0, 1.0)

        cumu_post = 0.0
        selected_link_index = 0
        for posterior in posteriors:
            cumu_post += posterior
            if cumu_post > r_sample:
                break
            selected_link_index += 1

        # self.logger.debug("SAMPLE: link index (%d/%d), random_sample: %f", selected_link_index, num_links, r_sample)
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

        # tell environment the site we are going to crawl
        self.tell('crawl_site', struct.unpack(">I", socket.inet_aton(site_url.rsplit('/', 1)[-1]))[0])

        # Setup the total number of links to crawl.  As a heuristic, it uses the number of links
        # from the first page * 2 as an upper bound.
        self._num_links_sampler.update(upper_bound=2*len(list(br.links())))
        num_links_to_crawl = self._num_links_sampler.sample()

        # now crawl for (max) num_links_to_crawl
        for _ in range(num_links_to_crawl):
            if self.interrupted:
                break

            page_links = list(br.links())
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
                br.follow_link(link=next_link)
            except Exception as ex:
                self.logger.warning("On follow_link: %s, (server: %s)", ex, site_url)
                break

        self.logger.info("Finished crawl at %s ...", site_url)
        self._visited_links.clear()  # clear set for next crawl
