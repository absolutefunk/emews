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

def make_config_cls(name, fields):
    '''
    Creates a class type for a configuration class.  Each eMews class which requires configuration
    will have its own type associated with it.
    Adapted from:
    stackoverflow.com/questions/2646157/what-is-the-fastest-to-access-struct-like-object-in-python
    except __getitem__ is removed as index based access is not required and we can potentially
    save some memory.
    '''
    conf_cls = textwrap.dedent("""\
    class {name}(object):
        __slots__ = {fields!r}
        def __init__(self, {args}):
            {self_fields} = {args}
    """).format(name=name, fields=fields, args=','.join(fields),
                self_fields=','.join('self.' + f for f in fields))
    exec_dict = {'fields': fields}
    exec conf_cls in exec_dict  # pylint: disable=W0122
    return exec_dict[name]
