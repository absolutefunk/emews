"""
Automates the process of a user interacting with an SSH client.

Automation includes logging in, executing some commands, and logging out.

Created on Feb 23, 2018
@author: Brian Ricks
"""
from pexpect import pxssh

import emews.services.baseservice


class AutoSSH(emews.services.baseservice.BaseService):
    """Classdocs."""

    __slots__ = ('_host', '_port', '_username', '_password', '_command_list',
                 '_num_commands_sampler', '_command_sampler', '_command_delay_sampler')

    def __init__(self, config):
        """Constructor."""
        super(AutoSSH, self).__init__()

        self._host = config['host']
        self._port = config['port']
        self._username = config['username']
        self._password = config['password']

        self._command_list = config['command_list']
        self._num_commands_sampler = self.sys.import_component(config['num_commands_sampler'])
        self._command_sampler = self.sys.import_component(config['command_sampler'])
        self._command_delay_sampler = self.sys.import_component(config['command_delay_sampler'])

    def _send_ssh_command(self, ssh_client, next_command):
        """Send the next SSH command, and set the command prompt."""
        ssh_client.sendline(next_command)

        if self.interrupted:
            return

        ssh_client.prompt()

    def run_service(self):
        """@Override Connect and login to the ssh server given with the credentials given."""
        try:
            ssh_client = pxssh.pxssh()
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("pxssh could not initialize: %s", ex)
            return

        if self.interrupted:
            return

        try:
            ssh_client.login(self._host,
                             self._username,
                             password=self._password,
                             port=self._port)
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("pxssh could not login to server: %s", ex)
            return

        # As we are sampling without replacement, we need to copy the original list
        command_list = list(self._command_list)

        # loop until command count reached
        num_commands = self._num_commands_sampler.sample()
        for _ in range(num_commands):
            if self.interrupted:
                break

            self._command_sampler.update(upper_bound=len(command_list) - 1)
            next_command = command_list.pop(self._command_sampler.sample())
            self.logger.debug("Next command: %s", next_command)

            try:
                self._send_ssh_command(ssh_client, next_command)
            except pxssh.ExceptionPxssh as ex:
                self.logger.warning("pxssh could not send ssh command: %s", ex)
                break

            self.sleep(self._command_delay_sampler.sample())

        self.logger.debug("Done executing commands, logging out...")

        try:
            ssh_client.logout()
        except pxssh.ExceptionPxssh as ex:
            self.logger.warning("pxssh could not log out from server: %s", ex)
