'''
Contains exceptions used by the emews system. All classes are located here for import convenience.

Created on Apr 22, 2018
@author: Brian Ricks
'''

class KeychainException(Exception):
    '''
    Raised when a key is missing along a keychain (ConfigComponent).
    '''
    pass

class MissingConfigException(Exception):
    '''
    Raised when an operation is called from the config object on the component config, and it's
    None.
    '''
    pass