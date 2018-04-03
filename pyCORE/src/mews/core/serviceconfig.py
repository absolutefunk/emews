'''
pyCORE service configuration.
Also wraps the pyCORE system configuration.

Created on Apr 2, 2018

@author: Brian Ricks
'''
import mews.core.iconfig

class ServiceConfig(mews.core.iconfig.IConfig):
    '''
    classdocs
    '''
    def __init__(self, sys_config):
        '''
        Constructor
        '''
        self._sys_config = sys_config
