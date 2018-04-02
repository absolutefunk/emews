'''
Containing thread for pyCORE service.

Created on Mar 5, 2018

@author: Brian Ricks
'''
from mews.core.services.basethread import BaseThread

class ServiceThread(BaseThread):
    '''
    classdocs
    '''

    def __init__(self, config, thr_name, service):
        '''
        Constructor
        '''
        super(ServiceThread, self).__init__(self, thr_name+"-"+service.__class__.__name__)
