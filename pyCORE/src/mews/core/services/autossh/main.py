'''
Created on Feb 26, 2018

@author: Brian Ricks
'''

import ConfigParser
import sys

import mews.core.services.autossh.autossh

if __name__ == '__main__':
    if not checkargs():
        sys.exit()

    config = ConfigParser.RawConfigParser()
    config.read(sys.argv[1])

    ssh_client = mews.core.services.autossh.autossh.AutoSSH()

    ssh_client.set_host(config.get('Server', 'host'))
    ssh_client.set_port(int(config.get('Server', 'port')))
    ssh_client.set_username(config.get('Server', 'username'))
    ssh_client.set_password(config.get('Server', 'password'))
    ssh_client.set_command_count(config.get('Options', 'command_count'))

    command_list_raw = config.items('Commands')
    command_list = []

    # populate the commmand_list frin the conf file
    for key_cmd, val_cmd in command_list_raw:
        command_list.append(val_cmd)

    ssh_client.set_command_list(config.COMMAND_LIST)

    # start a session of AutoSSH
    ssh_client.start()

def checkargs():
    '''
    Checks for valid command line arguments
    '''
    if len(sys.argv) != 2:
        print "[AutoSSH]: incorrect number of arguments\n"
    elif not sys.argv[1].startswith("--conf "):
        print "[AutoSSH]: argument does not specify configuration file"
    else:
        return True

    print "[AutoSSH]: usage: " + sys.argv[0] + "--conf <conf_file>"
    return False
