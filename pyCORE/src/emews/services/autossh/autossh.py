'''
AutoSSH: Automates the process of a user logging into an SSH server, executing some commands, and
logging out.  SSH server login rate and command execution rate are controlled by samplers set
in the config.

Created on Feb 23, 2018
@author: Brian Ricks
'''
import random

from pexpect import pxssh
import emews.services.baseservice

class AutoSSH(emews.services.baseservice.BaseService):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(AutoSSH, self).__init__(config)

        # parameter checks
        if self.config is None:
            self.logger.error("Service config is empty. Is a valid service config specified?")
            raise ValueError("Service config is empty")

        try:
            self._host = self.config.get('server', 'host')  # hostname of ssh server
            self._port = self.config.get('server', 'port')  # port of ssh server
            self._username = self.config.get('server', 'username')  # username for ssh login
            self._password = self.config.get('server', 'password')  # password for ssh login

            # distribution to sample list indices
            self._list_distribution = self.dependencies.get('command_sampler')
            # number of commands to execute before terminating
            self._command_count = self.config.get('command', 'command_count')
            # list of commands to execute
            self._command_list = self.config.get('command', 'command_list')
        except ValueError as ex:
            self.logger.error(ex)
            raise

    def run_service(self):
        '''
        @Override Attempts to connect and login to the ssh server given with the
        credentials given.
        '''
        try:
            ssh_client = pxssh.pxssh()
            ssh_client.login(self._host, self._username, password=self._password, port=self._port)

            # loop until command count reached
            for _ in range(self._command_count - 1):
                # check for event state first
                if self._event.is_set():
                    self.logger.debug("Caught stop request.")
                    break

                next_command = self._command_list[self._list_distribution.next_value()]
                self.logger.debug("Next Command: %s", next_command)

                ssh_client.sendline(next_command)
                ssh_client.prompt()
                print ssh_client.before

                # introduce a delay to simulate user looking at results before
                # typing next command
                self._event.wait(random.randint(1, 8))

            self.logger.debug("Done executing commands, logging out...")
            ssh_client.logout()
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("Exception with pxssh: %s", ex)
            return
