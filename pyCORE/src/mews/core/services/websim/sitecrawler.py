'''
Created on Jan 19, 2018

@author: Brian Ricks
'''

import random
import time
import mechanize

from mews.core.common.truncnorm_sampler import TruncnormSampler

class SiteCrawler(object):
    '''
    classdocs
    '''
    # prefix list for links which we should NOT visited
    _INVALID_LINK_PREFIX = ["java", "none"]

    def __init__(self):
        '''
        Constructor
        '''

        # class attributes
        self._br = mechanize.Browser()
        self._siteURL = None
        self._num_links_to_follow = None
        self._sigma = None
        self._path_sigma = None
        self._sampler = None

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

    def set_site(self, sitename):
        '''
        sets the URL to start crawling from
        '''
        self._siteURL = sitename

    def set_page_count(self, page_count):
        '''
        sets the number of links to follow
        '''
        self._num_links_to_follow = page_count

    def set_sigma(self, sigma):
        '''
        sets the sigma for link selection (first iteration)
        '''
        self._sigma = sigma

    def set_path_sigma(self, path_sigma):
        '''
        sets the sigma for link selection (past first iteration)
        '''
        self._path_sigma = path_sigma

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
        if self._siteURL is None:
            raise ValueError("[SiteCrawler]: siteURL cannot be blank")
        if self._num_links_to_follow is None or \
                not isinstance(self._num_links_to_follow, int) or \
                self._num_links_to_follow < 0:
            raise ValueError("[SiteCrawler]: page count must be a positive integer")

        self._br.open(self._siteURL)

        usePathSigma = False

        for _ in range(self._num_links_to_follow):
            page_links = list(self._br.links())

            # ie, if page_link length is zero
            if not page_links:
                print "[SiteCrawler]: Reached page without any links, stopping..."
                return

            if not usePathSigma:
                # first iteration
                self._sampler = TruncnormSampler(len(page_links) - 1, self._sigma)
                usePathSigma = True
            else:
                self._sampler.update_parameters(len(page_links) - 1, self._path_sigma)

            selected_link_index = 0
            while len(page_links) > 1:
                # keep looping until a valid link is found
                selected_link_index = self._sampler.next_value()

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
