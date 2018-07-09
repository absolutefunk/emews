'''
AutoSSH: Automates the process of a user logging into an SSH server, executing some commands, and
logging out.  SSH server login rate and command execution rate are controlled by samplers set
in the config.

Created on Feb 23, 2018
@author: Brian Ricks
'''
from pexpect import pxssh

import emews.base.exceptions
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
            raise emews.base.exceptions.MissingConfigException("No service config present.")

        try:
            self._host = self.config.get('server', 'host')  # hostname of ssh server
            self._port = self.config.get('server', 'port')  # port of ssh server
            self._username = self.config.get('server', 'username')  # username for ssh login
            self._password = self.config.get('server', 'password')  # password for ssh login

            # distribution to sample command list count
            self._num_commands = self.dependencies.get('num_commands_sampler')
            # distribution to sample list indices
            self._next_command = self.dependencies.get('command_sampler')
            self._next_command_std_dev = self.config.get('command_sampler', 'std_deviation')
            # distribution to sample delay to execute next command
            self._next_command_delay = self.dependencies.get('command_delay_sampler')

            # list of commands to execute
            self._command_list = self.config.get('command', 'command_list')
        except emews.base.exceptions.KeychainException as ex:
            self.logger.error(ex)
            raise

    def run_service(self):
        '''
        @Override Attempts to connect and login to the ssh server given with the
        credentials given.
        '''
        try:
            ssh_client = pxssh.pxssh()
            if self.interrupted:
                return

            ssh_client.login(self._host, self._username, password=self._password, port=self._port)

            # As we are sampling without replacement, we need to copy the original list
            command_list = list(self._command_list)

            # loop until command count reached
            num_commands = self._num_commands.next_value
            for _ in range(num_commands):
                if self.interrupted:
                    break

                self._next_command.update_parameters(
                    len(command_list) - 1, self._next_command_std_dev)
                next_command = command_list.pop(self._next_command.next_value)
                self.logger.debug("Next Command: %s", next_command)
                ssh_client.sendline(next_command)
                if self.interrupted:
                    break

                ssh_client.prompt()
                self.sleep(self._next_command_delay.next_value)

            self.logger.debug("Done executing commands, logging out...")
            ssh_client.logout()
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("pxssh raised exception: %s", ex)
