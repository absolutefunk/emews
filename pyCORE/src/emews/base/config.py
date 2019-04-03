"""
Configuration related module.

Created on Apr 3, 2018
@author: Brian Ricks
"""
import collections

from ruamel.yaml import YAML

import emews.base.import_tools


class SysProp(object):
    """Provides a read-only container for the system properties."""

    # All system properties defined here
    __slots__ = ('_logger',
                 '_node_name',
                 '_node_id',
                 '_root_path',
                 '_is_hub',
                 '_local')

    def __init__(self, **kwargs):
        """Constructor."""
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def import_component(self, config):
        """Given a config dict, return an instantiated component."""
        class_name = config['component'].split('.')[-1]
        module_path = 'emews.components.' + config['component'].lower()

        inject_dct = {}
        inject_dct['_sys'] = self
        inject_dct['logger'] = self._logger

        return emews.base.import_tools.import_class_from_module(
            module_path, class_name)(config['parameters'], _inject=inject_dct)

    # boilerplate for the properties (read-only)
    @property
    def logger(self):
        """Property."""
        return self._logger

    @property
    def node_name(self):
        """Property."""
        return self._node_name

    @property
    def node_id(self):
        """Property."""
        return self._node_id

    @property
    def root_path(self):
        """Property."""
        return self._root_path

    @property
    def is_hub(self):
        """Property."""
        return self._is_hub

    @property
    def local(self):
        """Property."""
        return self._local


def parse(filename):
    """Parse the given filename, and returns a structure representative of the YAML."""
    f = open(filename)

    yaml = YAML()
    strct = yaml.load(f)

    return _to_raw(strct)


def _to_raw(in_type):
    """Recursively convert input dictionary or list to a raw dictionary or list type."""
    if isinstance(in_type, collections.Mapping):
        # dict
        out_type = {}
        for key, value in in_type.iteritems():
            if isinstance(value, collections.Mapping):
                # dict
                out_type[key] = _to_raw(value)
            elif isinstance(value, list):
                # list
                out_type[key] = _to_raw(value)
            else:
                # primitive type
                out_type[key] = value
    else:
        # list
        out_type = []
        for value in in_type:
            if isinstance(value, collections.Mapping):
                # dict
                out_type.append(_to_raw(value))
            elif isinstance(value, list):
                # list
                out_type.append(_to_raw(value))
            else:
                # primitive type
                out_type.append(value)

    return out_type


# Config merging functions
def merge_configs(*config_dicts):
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
            merged_dict = config_dict['overrides']
            readonly_dict = config_dict['readonly']
            continue

        merged_dict = _section_merge(merged_dict, config_dict)

    # add in the read-only options
    _section_update_readonly(readonly_dict, merged_dict)
    return merged_dict


def _section_merge(sec1, sec2, keychain="root"):
    """
    Merge the first section with the second section given.

    A section is a dict.  Note that it is possible for a list to be passed that contains dicts.
    Currently, only dicts are considered to be sections, so lists are processed shallow, ie, any
    dicts or other lists, contained in the list will not be processed recursively.
    """
    new_section = {}

    for s1_key, s1_val in sec1.iteritems():
        s2_val = sec2.get(s1_key, None)  # if sec2 doesn't contain s1_key, or s1_key is None

        if s2_val is not None:
            if isinstance(s1_val, collections.Mapping):
                # s1_val is a section
                cur_kc = keychain + "-->" + str(s1_key)

                if not isinstance(s2_val, collections.Mapping):
                    raise TypeError("While parsing configuration at %s: Attempted override of"
                                    " section (map) with a non-section type (%s)."
                                    % (cur_kc, str(s2_val)))
                new_section[s1_key] = _section_merge(s1_val, s2_val, keychain=cur_kc)
            else:
                new_section[s1_key] = s2_val
        else:
            # nothing to merge
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
