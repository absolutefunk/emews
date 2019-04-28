"""
Base class for networking servers.

Created on Apr 2, 2019
@author: Brian Ricks
"""
from abc import abstractmethod

import emews.base.baseobject


class Handler(object):
    """Container for handler data."""

    __slots__ = ('callback', 'recv_list', 'send_type_str')

    def __init__(self, callback, format_str, send_type_str=None):
        """Constructor."""
        self.callback = callback  # callback to invoke once data is fully received
        self.recv_list = []  # tuples of (struct unpack string, recv_len)
        self.send_type_str = '>%s' % send_type_str if send_type_str is not None else None

        # split the format string if any type is 's' (string type)
        cur_format_str = ''
        prev_type = ''
        for type_chr in format_str:
            if type_chr == 's':
                if not (prev_type == 'H' or prev_type == 'I' or prev_type == 'L' or prev_type == 'Q'):
                    # a string has to have a length defined
                    raise AttributeError("Passed types_list contains a string without a valid len type (previous type in the list).")
                self.recv_list.append(('>' + cur_format_str, self._calc_recv_len(cur_format_str)))
                cur_format_str = ''
                self.recv_list.append(('s', 0))  # we don't know the recv_len yet
            else:
                cur_format_str += type_chr
                prev_type = type_chr

        if cur_format_str != '':
            self.recv_list.append(('>' + cur_format_str, self._calc_recv_len(cur_format_str)))

    def _calc_recv_len(self, format_str):
        """Calculate the number of bytes we should expected to receive."""
        recv_len = 0
        for type_chr in format_str:
            if type_chr == 'H' or type_chr == 'h':
                recv_len += 2
            elif type_chr == 'I' or type_chr == 'i' or type_chr == 'L' or type_chr == 'l' or type_chr == 'f':
                recv_len += 4
            elif type_chr == 'Q' or type_chr == 'q' or type_chr == 'd':
                recv_len += 8
            else:
                raise AttributeError("Format type '%s' in string '%s' not supported" % type_chr, format_str)

        return recv_len


class BaseServ(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_net_cache', '_net_client', 'handlers')

    def __init__(self):
        """Constructor."""
        self.handlers = None

    def handle_init(self, node_id, session_id):
        """Session init."""
        return self.serv_init(node_id, session_id)

    def handle_close(self, session_id):
        """Session termination."""
        self.serv_close(session_id)

    @abstractmethod
    def serv_init(self, node_id, session_id):
        """Return the first callback used for this server."""
        pass

    @abstractmethod
    def serv_close(self, session_id):
        """Handle any session closing tasks."""
        pass
