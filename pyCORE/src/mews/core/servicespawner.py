'''
Spawns new service threads and handles their management.

Created on Mar 24, 2018

@author: Brian Ricks
'''

import logging
import socket
from threading import Thread

from mews.core.services.servicecontrol import ServiceControl

class ServiceSpawner(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self._logger = logging.getLogger('pyCORE.base')

    def listen(self):
        '''
        Listens for new incoming services to spawn
        '''
