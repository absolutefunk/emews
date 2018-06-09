'''
CoreServices: classes which interface with the CORE network emulator, for automatic launching of
eMews clients (which themselves will send the proper commands to launch services)

Created on Mar 5, 2018
@author: Brian Ricks
'''

# Note, core in module path belongs to CORE, not emews
from core.service import CoreService

class AutoSSH(CoreService):
    '''
    CORE Service class for the eMews daemon
    '''
    _name = "AutoSSH_3"
    _group = "eMews"

    _configs = ("autossh_3.sh",)
    _startindex = 50  # make sure this is higher than the emews daemon CoreService
    _dirs = ()
    _startup = ("sh autossh_3.sh",)
    _shutdown = ()
    _validate = ()

    @classmethod
    def generateconfig(cls, node, filename, services):
        '''
        Generates the emews daemon per-node specific config.
        '''
        return """\
#!/bin/sh
export PYTHONPATH=/home/coreuser/
python /home/coreuser/emews/client/singleserviceclient.py -n %s -c autossh-3.yml AutoSSH
""" % (node.name)
