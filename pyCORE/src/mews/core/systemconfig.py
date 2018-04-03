'''
pyCORE system configuration.

Created on Mar 24, 2018

@author: Brian Ricks
'''
from abc import abstractmethod
import ConfigParser
import os

def parse(filename):
    '''
    Parses the given filename (if it exists), and returns a ConfigParser object with the data.
    '''

    if filename is None:
        return None

    cp = ConfigParser.SafeConfigParser()
    try:
        with open(filename) as f:
            cp.readfp(f)
    except ConfigParser.Error:
        f.close()
        raise

    f.close()

    return cp

def prepend_path(filename):
    '''
    Prepends an absolute path to the filename, relative to the directory this
    module was loaded from.
    '''
    path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    return os.path.join(path, filename)

class Config(object):
    '''
    classdocs
    '''
    def __init__(self, nodename):
        '''
        Constructor
        '''
        self.__cf = {
            'system': {
                # pyCORE config settings
                'PYCORE_PKG_PATH': 'mews.core',
                'PYCORE_PKG_SERVICES_PATH': 'mews.core.services',
                'BASE_LOGGER': 'pyCORE.base',
                'NODENAME_FORMAT': '%-12.12s',
                'NODENAME': nodename,
                'LOG_CONF': {
                    'version': 1,
                    'formatters': {
                        'default': {
                            'format': '[%(asctime)s] ' + '%-12.12s ' % nodename +
                                      '[%(levelname)-8.8s | %(module)-16.16s |'\
                                      ' %(funcName)-16.16s]: %(message)s'
                        }
                    },
                    'handlers': {
                        'console': {
                            'class': 'logging.StreamHandler',
                            'formatter': 'default',
                            'level': 'DEBUG',
                            'stream': 'ext://sys.stdout'
                        }
                    },
                    'loggers': {
                        '': {
                            'handlers': ['console'],
                            'level': 'DEBUG',
                        },
                        'pyCORE.base': {
                            'level': 'DEBUG',  # change this to INFO for production
                            'propagate': True
                        }
                    }
                }
            }
        }

    @property
    def logbase(self):
        '''
        returns the string representing the pyCORE base logger
        '''
        return self.__cf['system']['BASE_LOGGER']

    @property
    def nodename(self):
        '''
        returns the node name assigned
        '''
        return self.__cf['system']["NODENAME"]

    def get_sys(self, key):
        '''
        @Override Gets a value from the system section in the config dictionary.
        '''
        return self.__cf['system'][key]

    @abstractmethod
    def get(self, key, section=None):
        '''
        get a k/v from a section in the non-system space
        '''
        pass

    @abstractmethod
    def spawn_new(self, component_conf_file):
        '''
        spawns a new config object, with shared system config (self._cf) but new component config
        '''
        pass
