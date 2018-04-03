'''
pyCORE configuration.
Stores component configuration data.

Created on Apr 3, 2018

@author: Brian Ricks
'''

import mews.core.iconfig

class Config(mews.core.iconfig.IConfig):
    '''
    classdocs
    '''
    def __init__(self, nodename, component_config_filename):
        '''
        Constructor
        '''
        self.__component_config = mews.core.config.parse(
            mews.core.config.prepend_path(component_config_filename))

    def spawn_new(self, key, component_conf_file):
        '''
        spawns a new config object, with shared system config (self._cf) but new component config
        '''
