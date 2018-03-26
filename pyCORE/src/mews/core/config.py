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
    def __init__(self, nodename, filename):
        '''
        Constructor
        '''
        self._cf = {
            # pyCORE config settings
            'USER_CONF_SECTION': 'config',
            'BASE_LOGGER': 'pyCORE.base',
            'NODENAME_FORMAT': '%-12.12s',
            'NODENAME': nodename,
            'LOG_CONF': {
                'version': 1,
                'formatters': {
                    'default': {
                        'format': '[%(asctime)s] ' + '%-12.12s ' % nodename +
                                  '[%(levelname)-8.8s | %(module)-16.16s |'\
                                  ' %(funcName)-12.12s]: %(message)s'
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

        self._cf[self._cf['USER_CONF_SECTION']] = {}

        # add the k/v pairs to self._cf
        for key, value in cp.items(self._cf['USER_CONF_SECTION']):
            self._cf[self._cf['USER_CONF_SECTION']][key] = value

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
        return self._cf['LOG_CONF']

    @property
    def nodename(self):
        '''
        returns the node name assigned
        '''
        return self._cf["NODENAME"]
