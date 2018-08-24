'''
AutoSSH: Automates the process of a user logging into an SSH server, executing some commands, and
logging out.  SSH server login rate and command execution rate are controlled by samplers set
in the config.

Created on Feb 23, 2018
@author: Brian Ricks
'''
from pexpect import pxssh

import emews.services.baseservice

class AutoSSH(emews.services.baseservice.BaseService):
    '''
    classdocs
    '''
    def __init__(self, config, dependencies):
        '''
        Constructor
        '''
        super(AutoSSH, self).__init__()
        # parameter checks
        self._host = config.get('server', 'host')  # hostname of ssh server
        self._port = config.get('server', 'port')  # port of ssh server
        self._username = config.get('server', 'username')  # username for ssh login
        self._password = config.get('server', 'password')  # password for ssh login
        # list of commands to execute
        self._command_list = config.get('command', 'command_list')
        # distribution to sample command list count
        self._num_commands = dependencies.get('num_commands_sampler')
        # distribution to sample list indices
        self._next_command = dependencies.get('command_sampler')
        # distribution to sample delay to execute next command
        self._next_command_delay = dependencies.get('command_delay_sampler')

    def initialize(self, stage):
        '''
        @Override stage-specific initialization
        '''
        pass

    def _send_ssh_command(self, ssh_client, next_command):
        '''
        Sends the next SSH command, and sets the command prompt.
        Returns true if execution shoud continue, false otherwise.
        '''
        try:
            ssh_client.sendline(next_command)
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("pxssh could not send command: %s", ex)
            return False

        if self.interrupted:
            return False

        try:
            ssh_client.prompt()
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("pxssh could not set prompt: %s", ex)
            return False

        return True

    def run_service(self):
        '''
        @Override Attempts to connect and login to the ssh server given with the
        credentials given.
        '''
        try:
            ssh_client = pxssh.pxssh()
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("pxssh could not initialize: %s", ex)
            return

        if self.interrupted:
            return

        try:
            ssh_client.login(self._host, self._username, password=self._password, port=self._port)
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("pxssh could not login to server: %s", ex)
            raise

        # As we are sampling without replacement, we need to copy the original list
        command_list = list(self._command_list)

        # loop until command count reached
        num_commands = self._num_commands.next_value
        for _ in range(num_commands):
            if self.interrupted:
                break

            self._next_command.update_parameters(upper_bound=len(command_list) - 1)
            next_command = command_list.pop(self._next_command.next_value)
            self.logger.debug("Next Command: %s", next_command)

            if not self._send_ssh_command(ssh_client, next_command):
                return

            self.sleep(self._next_command_delay.next_value)

        self.logger.debug("Done executing commands, logging out...")

        try:
            ssh_client.logout()
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("pxssh cold not log out from server: %s", ex)
