'''
Configuration related module.

Created on Apr 3, 2018

@author: Brian Ricks
'''
import textwrap

from ruamel.yaml import YAML

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

def make_config_cls(name, fields_list):
    '''
    Creates a class type for an eMews object config.
    Adapted from:
    stackoverflow.com/questions/2646157/what-is-the-fastest-to-access-struct-like-object-in-python
    except __getitem__ is removed as index based access is not required and we can potentially
    save some memory.
    '''
    # TODO: support nested config dicts
    conf_cls = textwrap.dedent("""\
    class {name}(object):
        __slots__ = {fields!r}
        def __init__(self, {args}):
            {self_fields} = {args}
    """).format(name=name, fields=fields_list, args=','.join(fields_list),
                self_fields=','.join('self.' + f for f in fields_list))
    exec_dict = {'fields': fields_list}
    exec conf_cls in exec_dict  # pylint: disable=W0122
    return exec_dict[name]
