"""
Importer: importing / instantiation helper functions.

Created on Feb 5, 2019
@author: Brian Ricks
"""
import emews.base.import_tools


def instantiate(config):
    """Given a config dict, return an instantiated component as specified by the config dict."""
    class_name = config['component'].split('.')[-1]
    module_path = 'emews.components.' + config['component'].lower()
    return emews.base.import_tools.import_class_from_module(
        module_path, class_name)(config['parameters'])
