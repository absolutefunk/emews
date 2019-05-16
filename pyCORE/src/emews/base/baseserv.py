"""
Base class for networking servers.

Created on Apr 2, 2019
@author: Brian Ricks
"""
from abc import abstractmethod

import emews.base.baseobject


def calculate_recv_len(format_str):
    """Calculate the number of bytes we should expected to receive."""
    recv_len = 0
    for type_chr in format_str:
        if type_chr == '>':
            continue
        if type_chr == 'H' or type_chr == 'h':
            recv_len += 2
        elif type_chr == 'I' or type_chr == 'i' or type_chr == 'L' or type_chr == 'l' or type_chr == 'f':
            recv_len += 4
        elif type_chr == 'Q' or type_chr == 'q' or type_chr == 'd':
            recv_len += 8
        elif type_chr == 's':
            raise AttributeError("Format type 's' in string '%s' cannot be present to calculate length" % format_str)
        else:
            raise AttributeError("Format type '%s' in string '%s' not supported" % type_chr, format_str)

    return recv_len


def build_query(send_vals):
    """Build the query type string from a list of (send values, value type) tuples."""
    format_type_str = '>'
    val_list = []
    for val, val_type in send_vals.iteritems():
        if val_type == 's':
            format_type_str += 'L' + str(len(val)) + 's'  # 4 bytes for str len
            val_list.append(str(len(val)))
        else:
            format_type_str += val_type
        val_list.append(val)

    return (format_type_str, val_list)


class NetProto(object):
    """Specification for a server protocol."""

    __slots__ = ('proto_id', 'request_id', '_type_str', '_type_ret', '_len')

    def __init__(self, type_string, type_return=None, proto_id=-1, request_id=-1):
        """Constructor."""
        self.proto_id = proto_id
        self.request_id = request_id
        self._type_str = type_string
        self._type_ret = type_return
        self._len = len(type_string)

    @property
    def return_type(self):
        """Return the return type."""
        return self._type_ret

    @property
    def format_string(self):
        """Return the type_str."""
        return self._type_str

    def type_at(self, index):
        """Return the type at specified index."""
        return self._type_str[index]

    def __len__(self):
        """Return the length of the type_str string."""
        return self._len


class Handler(object):
    """Container for handler data."""

    __slots__ = ('callback', 'recv_types', 'protocol')

    def __init__(self, protocol, callback):
        """Constructor."""
        self.callback = callback  # callback to invoke once data is fully received
        self.recv_types = []  # tuples of (struct unpack type string, recv_len)
        self.protocol = protocol

        # split the format string if any type is 's' (string type)
        cur_format_str = ''
        for type_chr in protocol._type_str:
            if type_chr == 's':
                self.recv_types.append(
                    ('>%sL' % cur_format_str, calculate_recv_len(cur_format_str) + 4))
                cur_format_str = ''
                self.recv_types.append(('s', 0))  # we don't know the recv_len yet
            else:
                cur_format_str += type_chr

        if cur_format_str != '':
            self.recv_types.append(('>%s' % cur_format_str, calculate_recv_len(cur_format_str)))


class BaseServ(emews.base.baseobject.BaseObject):
    """Classdocs."""

    __slots__ = ('_net_cache', '_net_client', 'handlers', 'serv_id')

    def __init__(self):
        """Constructor."""
        super(BaseServ, self).__init__()
        self.handlers = None

    def handle_init(self, node_id, session_id):
        """Session init."""
        return self.serv_init(node_id, session_id)

    def handle_close(self, session_id):
        """Session termination."""
        self.serv_close(session_id)

    @abstractmethod
    def serv_init(self, node_id, session_id):
        """Server init."""
        pass

    @abstractmethod
    def serv_close(self, session_id):
        """Handle any session closing tasks."""
        pass
