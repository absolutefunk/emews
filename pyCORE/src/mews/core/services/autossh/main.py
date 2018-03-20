'''
Standalone driver for AutoSSH.  When using in CORE, launch through the
RunService class.

Created on Feb 26, 2018

@author: Brian Ricks
'''

import sys

import mews.core.services.autossh.autossh
import mews.core.services.runservice

if __name__ == '__main__':

    if not checkargs():
        sys.exit()

    ssh_client = mews.core.services.autossh.autossh.AutoSSH()
    ssh_client.configure(sys.argv[1])

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
