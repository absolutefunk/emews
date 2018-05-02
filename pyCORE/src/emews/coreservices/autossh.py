'''
CoreServices: classes which interface with the CORE network emulator, for automatic launching of
eMews clients (which themselves will send the proper commands to launch services)

Created on Mar 5, 2018

@author: Brian Ricks
'''

# Note, core in module path belongs to CORE, not emews
from core.services.utility import UtilService

class AutoSSHService(UtilService):
    '''
    CORE Service class for the AutoSSH service
    '''
    _name = "AutoSSH"

    _configs = ()
    _startindex = 20  # make sure this is higher than the emews daemon CoreService
    _dirs = ("/home/coreuser/emews")
    _startup = ("python client/singleserviceclient.py AutoSSH")
    _shutdown = ()
    _validate = ()
