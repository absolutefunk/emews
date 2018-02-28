'''
Created on Feb 26, 2018

@author: Brian Ricks
'''
import mews.core.services.autossh.autossh
import mews.core.services.autossh.conf as config

if __name__ == '__main__':
    ssh_client = mews.core.services.autossh.autossh.AutoSSH()

    ssh_client.set_host(config.HOST)
    ssh_client.set_port(config.PORT)
    ssh_client.set_username(config.USERNAME)
    ssh_client.set_password(config.PASSWORD)
    ssh_client.set_command_list(config.COMMAND_LIST)
    ssh_client.set_command_count(config.COMMAND_COUNT)

    ssh_client.start()
