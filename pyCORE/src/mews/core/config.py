'''
pyCORE configuration.

Created on Mar 24, 2018

@author: Brian Ricks
'''
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
    def __init__(self, nodename, filename=None):
        '''
        Constructor
        '''
        self._cf = {
            # pyCORE config settings
            'USER_CONF_SECTION_NAME': 'config',  # the section name in the conf file
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
            },
            'SYS_CONF_SECTION': {
                'LISTENER': {
                    'LISTENER_RECV_BUFFER': 2,
                    'COMMAND_DELIMITER': ' '
                }
            },
            'USER_CONF_SECTION': {}
        }

        self.__parse(filename)

    def __parse(self, filename):
        '''
        parse the config file
        '''
        cp = parse(filename)

        if cp is None:
            return

        # add the k/v pairs to self._cf (only from the 'USER_CONF_SECTION' in the conf file)
        for key, value in cp.items(self._cf['USER_CONF_SECTION_NAME']):
            self._cf['USER_CONF_SECTION'][key] = value

    def get(self, key):
        '''
        Gets a value from the user conf space.
        '''
        return self._cf['USER_CONF_SECTION'][key]

    def add_sys(self, section, key, value):
        '''
        Adds a k/v to the section given under SYS_CONF_SECTION.  If the key already exists,
        an exception is thrown.
        '''
        if not section in self._cf['SYS_CONF_SECTION']:
            self._cf['SYS_CONF_SECTION'][section] = {}
        elif key in self._cf['SYS_CONF_SECTION'][section]:
            raise ValueError("Key %s already exists in section %s." % (key, section))

        self._cf['SYS_CONF_SECTION'][section][key] = value

    def get_sys(self, section, key):
        '''
        Gets a value from the sys conf space, given a section and key.
        '''
        return self._cf['SYS_CONF_SECTION'][section][key]

    def get_sys_section(self, section):
        '''
        Gets a dict from the sys conf space, given a section.
        '''
        return self._cf['SYS_CONF_SECTION'][section]

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
