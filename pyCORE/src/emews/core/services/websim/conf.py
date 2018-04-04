'''
Configuration file for websim SiteCrawler

Created on Feb 26, 2018

@author: Brian Ricks
'''
# site address to start crawling from
START_SITE = "https://www.cmu.edu/silicon-valley"
# number of sequential links to follow when crawling
PAGE_COUNT = 5
# std deviation of picking a link around mu (from list of links)
LINK_STDDEV = 2.0
# std deviation of picking a link around mu in a path of links (after first iteration)
PATH_LINK_STDDEV = 0.5
