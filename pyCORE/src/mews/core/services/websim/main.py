'''
Created on Jan 19, 2018

@author: Brian Ricks
'''
import mews.core.services.websim.sitecrawler

if __name__ == '__main__':
    crawler = mews.core.services.websim.sitecrawler.SiteCrawler()

    crawler.setsite("https://www.cmu.edu/silicon-valley")
    crawler.site_crawl()
