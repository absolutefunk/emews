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
            ssh_client.login(self.config.host,
                             self.config.username,
                             password=self.config.password,
                             port=self.config.port)
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("pxssh could not login to server: %s", ex)
            raise

        # As we are sampling without replacement, we need to copy the original list
        command_list = list(self.config.command_list)

        # loop until command count reached
        num_commands = self.helpers.num_commands_sampler.sample()
        for _ in range(num_commands):
            if self.interrupted:
                break

            self.helpers.command_sampler.update_parameters(upper_bound=len(command_list) - 1)
            next_command = command_list.pop(self.helpers.command_sampler.sample())
            self.logger.debug("Next Command: %s", next_command)

            if not self._send_ssh_command(ssh_client, next_command):
                return

            self.sleep(self.helpers.command_delay_sampler.sample())

        self.logger.debug("Done executing commands, logging out...")

        try:
            ssh_client.logout()
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("pxssh could not log out from server: %s", ex)
