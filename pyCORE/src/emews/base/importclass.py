'''
Helper module for importing classes from a string.

Created on Apr 13, 2018

@author: Brian Ricks
'''
import importlib

def import_class(class_path, class_name):
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

def import_class_from_module(class_path, class_name=None):
    '''
    Attempts to import a class given the class name and path.  Does not assume that module name is
    the same as the class name, instead assumes that the class_path includes the module.  If the
    class_name is not given, then assume the class name itself is part of the class_path.
    '''
    if class_name is None:
        class_path, class_name = class_path.rsplit(".", 1)

    # resolve the class module
    class_module = importlib.import_module(class_path)
    # resolve the class
    return getattr(class_module, class_name)
