'''
Created on Jan 19, 2018

@author: Brian Ricks
'''

import random
import time
import scipy.stats
import mechanize

class SiteCrawler(object):
    '''
    classdocs
    '''
    # number of sequential links to follow when crawling
    _DEFAULT_PAGE_COUNT = 5
    # std deviation of picking a link around mu (from list of links)
    _DEFAULT_LINK_STDDEV = 0.8
    # std deviation of picking a link around mu in a path of links (after first iteration)
    _DEFAULT_PATH_LINK_STDDEV = 0.2
    # prefix list for links which we should NOT visited
    _INVALID_LINK_PREFIX = ["java", "none"]

    def __init__(self):
        '''
        Constructor
        '''

        # class attributes
        self._br = mechanize.Browser()
        self._siteURL = None
        self._num_links_to_follow = self._DEFAULT_PAGE_COUNT

        self.init_config()

    def init_config(self):
        '''
        init configuration params
        '''

        # no, I am not a robot ;-)
        self._br.set_handle_robots(False)
        # set user agent string to something real-world
        self._br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Ubuntu; Linux \
        x86_64; rv:57.0) Gecko/20100101 Firefox/57.0')]

    def setsite(self, sitename):
        '''
        sets the URL to start crawling from
        '''

        self._siteURL = sitename

    def truncnorm_link_index(self, num_links, itr=None):
        '''
        selects the link index to visit next
        '''

        mu = (num_links - 1) / 2.0  # pick the middle link to distribute around

        if itr is not None and itr > 0:
            sigma = self._DEFAULT_PATH_LINK_STDDEV
        else:
            sigma = self._DEFAULT_LINK_STDDEV  # default stddev

        lower = 0  # lower bound
        upper = num_links - 1  # upper bound

        dist = scipy.stats.truncnorm(
            (lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)

        return int(round(dist.rvs(1)[0]))

    def checklink(self, link_str):
        '''
        checks a link object's URL for validity (not a javascript link or something)
        that we can't visit
        '''

        for prefix in self._INVALID_LINK_PREFIX:
            if link_str.absolute_url.lower().startswith(prefix):
                return False

        return True

    def site_crawl(self):
        '''
        crawls a web site, starting from the _siteURL, picking links from
        each page visited
        '''
        self._br.open(self._siteURL)

        for itr in range(self._num_links_to_follow):
            page_links = list(self._br.links())

            # ie, if page_link length is zero
            if not page_links:
                print "[SiteCrawler]: Reached page without any links, stopping..."
                return

            selected_link_index = 0

            while len(page_links) > 1:
                # keep looping until a valid link is found
                selected_link_index = self.truncnorm_link_index(len(page_links), itr=itr)

                # print page_links[selected_link_index].base_url
                if self.checklink(page_links[selected_link_index]):
                    break

                # strip the bad link from the list and try again
                del page_links[selected_link_index]

            if not page_links:
                print "[SiteCrawler]: Reached page with links, but none were valid, stopping..."
                return

            next_link = page_links[selected_link_index]

            # introduce a delay to simulate user moving mouse and clicking link
            time.sleep(random.randint(1, 8))

            print "[" + str(selected_link_index) + "/" + str(len(page_links)) + "]: " \
            + next_link.absolute_url

            self._br.follow_link(link=next_link)
