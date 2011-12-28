# Copyright (c) 2012 Chris Lucas, <chris@chrisjlucas.com>
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#from rtorrent.rpc import Method
import rtorrent.rpc

Method = rtorrent.rpc.Method

class Peer:
    """Represents an individual peer within a L{Torrent} instance."""
    def __init__(self, _rt_obj, info_hash, **kwargs):
        self._rt_obj = _rt_obj
        self._p = self._rt_obj._p #: X{ServerProxy} instance
        self.info_hash = info_hash #: info hash for the torrent the peer is associated with
        for k in kwargs.keys():
            setattr(self, k, kwargs.get(k, None))

        self.rpc_id = "{0}:p{1}".format(self.info_hash, self.id) #: unique id to pass to rTorrent

        self._method_list = self._rt_obj._method_dict[self.__class__.__name__]
        rtorrent.rpc._build_rpc_methods(self, self._method_list)

    def __repr__(self):
        return("<Peer id={0}>".format(self.id))

    def update(self):
        """Refresh peer data
        
        @note: All fields are stored as attributes to self.

        @return: None
        """
        multicall = rtorrent.rpc.Multicall(self._rt_obj)
        retriever_methods = [m for m in self._method_list \
                        if m.is_retriever() and m.is_available(self._rt_obj)]
        for method in retriever_methods:
            multicall.add(method, self.rpc_id)

        result = multicall.call()
        for m, r in zip(retriever_methods, result):
            setattr(self, m.varname, rtorrent.rpc.process_result(m, r))

methods = [
    # RETRIEVERS
    Method(Peer, 'is_preferred', 'p.is_preferred', None, boolean=True),
    Method(Peer, 'get_down_rate', 'p.get_down_rate', None),
    Method(Peer, 'is_unwanted', 'p.is_unwanted', None, boolean=True),
    Method(Peer, 'get_peer_total', 'p.get_peer_total', None),
    Method(Peer, 'get_peer_rate', 'p.get_peer_rate', None),
    Method(Peer, 'get_port', 'p.get_port', None),
    Method(Peer, 'is_snubbed', 'p.is_snubbed', None, boolean=True),
    Method(Peer, 'get_id_html', 'p.get_id_html', None),
    Method(Peer, 'get_up_rate', 'p.get_up_rate', None),
    Method(Peer, 'is_banned', 'p.banned', None, boolean=True),
    Method(Peer, 'get_completed_percent', 'p.get_completed_percent', None),
    Method(Peer, 'completed_percent', 'p.completed_percent', None),
    Method(Peer, 'get_id', 'p.get_id', None),
    Method(Peer, 'is_obfuscated', 'p.is_obfuscated', None, boolean=True),
    Method(Peer, 'get_down_total', 'p.get_down_total', None),
    Method(Peer, 'get_client_version', 'p.get_client_version', None),
    Method(Peer, 'get_address', 'p.get_address', None),
    Method(Peer, 'is_incoming', 'p.is_incoming', None, boolean=True),
    Method(Peer, 'is_encrypted', 'p.is_encrypted', None, boolean=True),
    Method(Peer, 'get_options_str', 'p.get_options_str', None),
    Method(Peer, 'get_client_version', 'p.client_version', None),
    Method(Peer, 'get_up_total', 'p.get_up_total', None),

    # testing
    Method(Peer, 'fake_method', 'p._fake_method', None),

    # MODIFIERS
]
