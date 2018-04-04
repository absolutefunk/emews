'''
Created on Jan 19, 2018

@author: Brian Ricks
'''
import emews.core.services.websim.sitecrawler
import emews.core.services.websim.conf as config

if __name__ == '__main__':
    crawler = emews.core.services.websim.sitecrawler.SiteCrawler()

    crawler.set_site(config.START_SITE)
    crawler.set_sigma(config.LINK_STDDEV)
    crawler.set_path_sigma(config.PATH_LINK_STDDEV)
    crawler.set_page_count(config.PAGE_COUNT)
    crawler.site_crawl()
