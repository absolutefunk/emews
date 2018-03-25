'''
Configuration dictionary for the logging system.

Created on Mar 24, 2018

@author: Brian Ricks
'''

log_config = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] <NodeName> [%(levelname)-8.8s ' \
            '| %(module)-16.16s | %(funcName)-12.12s]: %(message)s',
            'nodename-format': '%-12.12s'
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
