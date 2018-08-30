'''
Configuration related module.

Created on Apr 3, 2018

@author: Brian Ricks
'''
from ruamel.yaml import YAML

'''
Module-level functions related to configuration loading/parsing.
'''
def parse(filename):
    '''
    Parses the given filename (if it exists), and returns a dictionary.
    '''
    if filename is None:
        return None

    f = open(filename)

    yaml = YAML()
    dct = yaml.load(f)

    return dct
