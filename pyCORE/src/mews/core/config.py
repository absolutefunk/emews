'''
pyCORE configuration.

Created on Mar 24, 2018

@author: Brian Ricks
'''
import ConfigParser

class Config(object):
    '''
    classdocs
    '''
    def __init__(self, filename):
        '''
        Constructor
        '''
        self._cf = {
            # pyCORE config settings
            'USER_CONF_SECTION': 'config',
            'BASE_LOGGER': 'pyCORE.base',
            'NODENAME_FORMAT': '%-12.12s',
            'NODENAME_IDENT': '<NodeName>',
            'nodename': '',
            'log': {
                'version': 1,
                'formatters': {
                    'default': {
                        'format': '[%(asctime)s] <NodeName> [%(levelname)-8.8s ' \
                        '| %(module)-16.16s | %(funcName)-12.12s]: %(message)s'
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

        self.__parse(filename)

    def __setnodename(self, nodename):
        '''
        Sets the node name for logging.
        This expects that the user conf (which has the node name) is already
        parsed and appended to _cf.
        '''
        self._cf['nodename'] = nodename
        self._cf['log']['formatters']['default']['format'].replace(
            self._cf['NODENAME_IDENT'],
            (self.__cf['NODENAME_FORMAT'] % self._cf['nodename']))

    def __parse(self, filename):
        '''
        parse the config file
        '''
        cp = ConfigParser.SafeConfigParser()
        try:
            with open(filename) as f:
                cp.readfp(f)
        except ConfigParser.Error:
            f.close()
            raise

        f.close()

        self._cp[self._cp['USER_CONF_SECTION']] = {}

        # add the k/v pairs to self._cf
        for key, value in cp.items(self._cf['USER_CONF_SECTION']):
            self._cp['USER_CONF_SECTION'][key] = value

    def get(self, key):
        '''
        Gets a value from the user conf space.
        '''
        return self._cf[self._cf['USER_CONF_SECTION']][key]

    # specific getters
    @property
    def logbase(self):
        '''
        returns the string representing the pyCORE base logger
        '''
        return self._cf['BASE_LOGGER']

    @property
    def logconfig(self):
        '''
        returns the logging configuration
        '''
        return self._cf['log']

    @property
    def nodename(self):
        '''
        returns the node name assigned
        '''
        return self._cf["nodename"]
