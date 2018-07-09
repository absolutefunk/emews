'''
Helper module for importing classes from a string.

Created on Apr 13, 2018

@author: Brian Ricks
'''
import importlib

def import_class(class_name, class_path):
    '''
    Attempts to import a class given the class name and path.  Assumes that module name is the same
    as the class name, but all lower case.
    '''
    module_name = class_name.lower()
    class_module_loc = class_path + "." + module_name

    # resolve the class module
    class_module = importlib.import_module(class_module_loc)
    # resolve the class
    return getattr(class_module, class_name)

def import_class_from_module(class_name, class_path):
    '''
    Attempts to import a class given the class name and path.  Does not assume that module name is
    the same as the class name, instead assumes that the class_path includes the module.
    '''
    # resolve the class module
    class_module = importlib.import_module(class_path)
    # resolve the class
    return getattr(class_module, class_name)
