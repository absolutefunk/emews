"""
Functions for importing classes from strings.

Created on Apr 13, 2018

@author: Brian Ricks
"""
import importlib

import emews.base.baseobject


def import_class(class_path, class_name):
    """
    Attempt to import a class given the class name and path.

    Assumes that module name is the same as the class name, but all lower case.
    """
    module_name = class_name.lower()
    class_module_loc = class_path + "." + module_name

    # resolve the class module
    class_module = importlib.import_module(class_module_loc)
    # resolve the class
    return getattr(class_module, class_name)


def import_class_from_module(module_path, class_name=None):
    """
    Attempt to import a class given the class name and module path.

    Does not assume that module name is the same as the class name, instead assumes that the
    module_path includes the module.  If the class_name is not given, then assume the class name
    itself is part of the module_path.
    """
    if class_name is None:
        module_path, class_name = module_path.rsplit(".", 1)

    # resolve the class module
    class_module = importlib.import_module(module_path)
    # resolve the class
    return getattr(class_module, class_name)


def import_service(service_name):
    """
    Attempt to import an eMews service given the service name.

    Service must be in a folder of the same name, in the eMews services folder.
    """
    class_path = emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.service_path + "." + \
        service_name.lower()

    return import_class(class_path, service_name)
