'''
Provides a centralized point for distributed log collection over a network.

Only one node will have a LogServer.  The system.yml config will specify the node.  The other nodes
will be able to look up the logserver node, and forward log entries to it.

When using distributed logging, the formatting configuration in system.yml would be applied to
LogServer if LogServer is the final destination for the log entries.  If LogServer is acting as a
collection and forward server, then no formatting is applied.

Created on Apr 22, 2018
@author: Brian Ricks
'''
import emews.base.spawninglistener

class LogServer(emews.base.spawninglistener.SpawningListener):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(LogServer, self).__init__(config)

    def update_spawnclass_args(self):
        '''
        @Override
        '''
