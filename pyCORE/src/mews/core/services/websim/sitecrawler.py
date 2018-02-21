'''
Created on Jan 19, 2018

@author: Brian Ricks
'''
import math
import mechanize
import random
import scipy.stats
import time


class SiteCrawler(object):
    '''
    classdocs
    '''
    _DEFAULT_PAGE_COUNT = 5  # number of sequential links to follow when crawling
    _DEFAULT_LINK_STDDEV = 0.8  # std deviation of picking a link around mu (from list of links)
    _DEFAULT_PATH_LINK_STDDEV = 0.2  # std deviation of picking a link around mu in a path of links (after first iteration)

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
        # no, I am not a robot ;-)
        self._br.set_handle_robots(False)
        # set user agent string to something real-world
        self._br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0')]

    def setsite(self, sitename):
        self._siteURL = sitename

    def truncnorm_link_index(self, num_links, itr = None):
        mu = (num_links - 1) / 2.0  # pick the middle link to distribute around

        if itr is not None and itr > 0:
            sigma = self._DEFAULT_PATH_LINK_STDDEV
        else:
            sigma = self._DEFAULT_LINK_STDDEV  # default stddev

        lower = 0  # lower bound
        upper = num_links - 1  # upper bound

        dist = scipy.stats.truncnorm((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)

        return int(round(dist.rvs(1)[0]))

    def checklink(self, link_str):
        # TODO: generalize this as a list
        
        if link_str.absolute_url.lower().startswith("java"):
            return False

        return True

    def site_crawl(self):
        self._br.open(self._siteURL)

        for itr in range(self._num_links_to_follow):
            page_links = list(self._br.links())

            if len(page_links) == 0:
                print "[SiteCrawler]: Reached page without any links, stopping..."
                return

            selected_link_index = 0

            while len(page_links) > 1:
                # keep looping until a valid link is found
                selected_link_index = self.truncnorm_link_index(len(page_links), itr = itr)

                #print page_links[selected_link_index].base_url
                if self.checklink(page_links[selected_link_index]):
                    break

                # strip the bad link from the list and try again
                del page_links[selected_link_index]

            if len(page_links) == 0:
                print "[SiteCrawler]: Reached page with links, but none were valid, stopping..."
                return

            next_link = page_links[selected_link_index]

            # introduce a delay to simulate user moving mouse and clicking link
            time.sleep(random.randint(1,8))

            print "[" + str(selected_link_index) + "/" + str(len(page_links)) + "]: " + next_link.absolute_url
            self._br.follow_link(link = next_link)
