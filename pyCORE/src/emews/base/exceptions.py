'''
Contains exceptions used by the eMews system. All classes are located here for import convenience.

Created on Apr 22, 2018
@author: Brian Ricks
'''
class ServiceShutdownException(Exception):
    '''
    Raised when a service has passed the timeout period to shutdown gracefully.  If catching this,
    shutdown should be immediate, otherwise a potentially long, unanticipated wait could ensue.
    '''
    pass
