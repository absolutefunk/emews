"""
Configuration related module.

Created on Apr 3, 2018
@author: Brian Ricks
"""
import collections

from ruamel.yaml import YAML


def parse(filename):
    """Parse the given filename (if it exists), and returns a dictionary."""
    if filename is None:
        return None

    f = open(filename)

    yaml = YAML()
    dct = yaml.load(f)

    return _to_raw_dict(dct)


def _to_raw_dict(in_dict):
    """Recursively convert input dictionary to a raw dictionary type."""
    out_dict = {}
    for key, value in in_dict.items():
        if isinstance(value, collections.Mapping):
            # recursively replace with raw dictionary type
            out_dict[key] = _to_raw_dict(value)

    return out_dict

# TODO: possibly move this to another module
class InjectionMeta(type):
    """
    Meta class for configuration dependency injection.

    Dependency Injection is performed before any child class __init__ methods are called.
    Config object injected through constructor, but processed first using an __init__ override.
    """

    def __new__(mcs, name, bases, namespace, **kwargs):
        """Override __init__ in subclass with below definition."""
        new_cls = super(InjectionMeta, mcs).__new__(mcs, name, bases, namespace, **kwargs)
        # store a reference to the subclass __init__
        subcls_init = new_cls.__init__

        def __init__(self, *args, **kwargs):
            """
            Injected Constructor from InjectionMeta.

            Used to inject configuration before the original subclass __init__ is called.  This way
            the configuration is available without the dev having to explicitly handle a config
            object on __init__.
            """
            # As a derived class could pass their own '_inject' k/v, we not only check for the key,
            # but whether the _config attribute exists already.
            if '_inject' in kwargs and not hasattr(self, '_di_config'):
                # pop the key so the class doesn't get it through **kwargs
                inject_dict = kwargs.pop('_inject')
                # 'config' is a required key
                self._di_config = inject_dict['config']  # pylint: disable=W0212
                # optional keys
                if 'helpers' in inject_dict:
                    self._di_helpers = inject_dict['helpers']  # pylint: disable=W0212
                if 'extra' in inject_dict:
                    # these are class-specific attributes, could be anything
                    for attr_name, attr_value in inject_dict['extra']:
                        setattr(self, attr_name, attr_value)

            subcls_init(self, *args, **kwargs)

        setattr(new_cls, '__init__', __init__)  # replace subclass init with this one
        return new_cls


## Config merging functions
def merge_configs(merge_type, *config_dicts):
    """
    Merge the input config files by key, in order of precedence.

    Precedence order: base config, system config, node config.
    For example, values in node config could override values in system config.
    """
    if len(config_dicts) < 2:
        # must be at least two dicts to merge
        raise ValueError("At least two dicts must be passed.")

    first_dict = True
    merged_dict = None
    readonly_dict = None
    for config_dict in config_dicts:
        if first_dict:
            first_dict = False
            # first dict is assumed to be the base config dict
            merged_dict = config_dict[merge_type]['overrides']
            readonly_dict = config_dict[merge_type]['readonly']
            continue

        merged_dict = _section_merge(merged_dict, config_dict)

    # add in the read-only options
    _section_update_readonly(readonly_dict, merged_dict)
    return merged_dict

def _section_merge(sec1, sec2, keychain="root"):
    """
    Merge the first section with the second section given.  A section is a dict.

    This is a recursive procedure; the section depth should not be that great.
    """
    new_section = {}

    for s1_key, s1_val in sec1.iteritems():
        s2_val = sec2.get(s1_key, None)  # if sec2 doesn't contain s1_key, or s1_key is None

        if isinstance(s1_val, collections.Mapping):
            # s1_val is a section
            cur_kc = keychain + str(s1_key)

            if not isinstance(s2_val, collections.Mapping):
                raise TypeError("While parsing configuration at %s: Attempted override of section with a non-section type." % cur_kc)

            if s2_val is None:
                # this ensures the resulting section is a basic dict
                new_section[s1_key] = _section_merge(s1_val, {}, keychain=cur_kc)
            else:
                new_section[s1_key] = _section_merge(s1_val, s2_val, keychain=cur_kc)

        elif s2_val is not None:
            if s1_val is not None and not isinstance(s1_val, s2_val.__class__):
                # if s1_val is None, then just overwrite it with s2_val
                raise ValueError("Type mismatch of config value for key '%s'. Must be %s." % (s_key, type(s_val)))

            new_section[s1_key] = s2_val
        else:
            # s1_val not a section and s1_key either not present in sec2 or s2_val is None
            new_section[s1_key] = s1_val

    return new_section

def _section_update_readonly(readonly_sec, merged_sec):
    """
    Add the readonly keys to the merged dict.

    This is a recursive procedure; the section depth should not be that great.
    """
    for s_key, s_val in readonly_sec.iteritems():
        if isinstance(s_val, collections.Mapping):
            # s_val is a dict (section)
            if s_key not in merged_sec:
                merged_sec[s_key] = {}
            _section_update_readonly(s_val, merged_sec[s_key])
        else:
            if merged_sec.get(s_key, None) is not None:
                raise ValueError("Cannot override values of read-only keys.  Key: '%s'." % s_key)
            merged_sec[s_key] = s_val
