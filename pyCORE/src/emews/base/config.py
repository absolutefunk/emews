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
        else:
            out_dict[key] = value

    return out_dict


class ConfigDict(collections.Mapping):
    """Provides a read-only dict structure."""

    def __init__(self, dct):
        """Constructor."""
        self._dct = dct

    def __getitem__(self, key):
        """Index notation."""
        return self._dct[key]

    def __len__(self):
        """Size of _dct."""
        return len(self._dct)

    def __iter__(self):
        """Provide _dct iterator."""
        return iter(self._dct)


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
    Merge the first section with the second section given.  A section is a dict.

    This is a recursive procedure; the section depth should not be that great.
    """
    new_section = {}

    for s1_key, s1_val in sec1.iteritems():
        s2_val = sec2.get(s1_key, None)  # if sec2 doesn't contain s1_key, or s1_key is None

        if isinstance(s1_val, collections.Mapping):
            # s1_val is a section
            cur_kc = keychain + "-->" + str(s1_key)

            if s2_val is not None:
                if not isinstance(s2_val, collections.Mapping):
                    raise TypeError("While parsing configuration at %s: Attempted override of "
                                    " section with a non-section type (%s)."
                                    % (cur_kc, str(s2_val)))
                new_section[s1_key] = _section_merge(s1_val, s2_val, keychain=cur_kc)

            else:
                # this ensures the resulting section is a basic dict
                new_section[s1_key] = _section_merge(s1_val, {}, keychain=cur_kc)

        elif s2_val is not None:
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
