'''
Created on Feb 23, 2018

@author: Brian Ricks
'''

import ConfigParser
import random
from threading import Event

from pexpect import pxssh
import mews.core.common.sequential_iterator as default_sampler
from mews.core.services.baseservice import BaseService

class AutoSSH(BaseService):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''

        # class attributes
        self._s = pxssh.pxssh()

        self._host = None  # hostname of ssh server
        self._port = None  # port of ssh server

        self._username = None  # username for ssh login
        self._password = None  # password for ssh login

        self._list_distribution = None  # distribution to sample list indices
        self._command_count = None  # number of commands to execute before terminating
        self._command_list = None  # list of commands to execute

        self._event = Event()  # used for sleep (interuptable)

    def set_host(self, host):
        '''
        sets the host of the ssh server
        '''
        self._host = host

    def set_port(self, port):
        '''
        sets the port of the ssh server
        '''
        self._port = port

    def set_username(self, username):
        '''
        sets the username to use for ssh login
        '''
        self._username = username

    def set_password(self, password):
        '''
        sets the password to use for ssh login
        '''
        self._password = password

    def set_command_distribution(self, distribution):
        '''
        sets the distribution used to sample command indices from
        '''

        self._list_distribution = distribution

    def set_command_count(self, command_count):
        '''
        sets the distribution used to sample command indices from
        '''

        self._command_count = command_count

    def set_command_list(self, command_list):
        '''
        sets list with commands which we will use for ssh sessions
        '''

        self._command_list = command_list
    def stop(self):
        '''
        Alerts the service that it has been called to stop.
        '''
        # interupt the event blocking
        self._event.set()

    def needs_config(self):
        '''
        returns true as this service needs a config file
        '''
        return True

    def configure(self, config_file=None):
        '''
        sets up the service for running, which means parsing a config file
        '''
        config = ConfigParser.RawConfigParser()
        config.read(config_file)

        self.set_host(config.get('Server', 'host'))
        self.set_port(int(config.get('Server', 'port')))
        self.set_username(config.get('Server', 'username'))
        self.set_password(config.get('Server', 'password'))
        self.set_command_count(config.get('Options', 'command_count'))

        command_list_raw = config.items('Commands')
        command_list = []

        # populate the commmand_list frin the conf file
        for _, val_cmd in command_list_raw:
            command_list.append(val_cmd)

        self.set_command_list(config.COMMAND_LIST)

    def start(self):
        '''
        attempts to connect and login to the ssh server given with the
        credentials given
        '''

        if self._host is None:
            raise ValueError("[AutoSSH]: Host cannot be empty")
        if self._port is None or not isinstance(self._port, int) or \
                not 0 <= self._port <= 65535:
            raise ValueError("[AutoSSH]: Port must be an integer between [0-65535]")
        if self._username is None:
            raise ValueError("[AutoSSH]: Username cannot be empty")
        if self._password is None:
            raise ValueError("[AutoSSH]: Password cannot be empty")
        if self._command_count is None or not isinstance(self._command_count, int) or \
                self._command_count < 0:
            raise ValueError("[AutoSSH]: Command count must be a positive integer")
        if self._command_list is None or not isinstance(self._command_list, list):
            raise ValueError("[AutoSSH]: Command list must be a list")

        self._s.login(self._host, self._username, password=self._password, port=self._port)

        if self._list_distribution is None:
            self._list_distribution = default_sampler.SequentualIterator(
                0, len(self._command_list))

        # loop until command count reached
        for _ in range(self._command_count - 1):
            # check for event state first
            if self._event.is_set():
                print "[AutoSSH]: caught stop request"
                break

            next_command = self._command_list[self._list_distribution.next_value()]
            print "[AutoSSH]: Next Command: " + next_command

            self._s.sendline(next_command)
            self._s.prompt()
            print self._s.before

            # introduce a delay to simulate user looking at results before
            # typing next command
            self._event.wait(random.randint(1, 8))

        print "[AutoSSH]: Done executing commands, logging out..."
        self._s.logout()