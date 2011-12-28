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

class Tracker:
    """Represents an individual tracker within a L{Torrent} instance."""

    def __init__(self, _rt_obj, info_hash, **kwargs):
        self._rt_obj = _rt_obj
        self._p = self._rt_obj._p #: X{ServerProxy} instance
        self.info_hash = info_hash #: info hash for the torrent using this tracker
        for k in kwargs.keys():
            setattr(self, k, kwargs.get(k, None))

        # for clarity's sake...
        self.index = self.group #: position of tracker within the torrent's tracker list
        self.rpc_id = "{0}:t{1}".format(self.info_hash, self.index) #: unique id to pass to rTorrent

        self._method_list = self._rt_obj._method_dict[self.__class__.__name__]
        rtorrent.rpc._build_rpc_methods(self, self._method_list)

    def __repr__(self):
        return("<Tracker index={0}, url=\"{1}\">".format(self.index, self.url))

    def enable(self):
        """Alias for set_enabled("yes")"""
        self.set_enabled("yes")
    def disable(self):
        """Alias for set_enabled("no")"""
        self.set_enabled("no")

    def update(self):
        """Refresh tracker data
        
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
    Method(Tracker, 'is_enabled', 't.is_enabled', None, boolean=True),
    Method(Tracker, 'get_id', 't.get_id', None),
    Method(Tracker, 'get_scrape_incomplete', 't.get_scrape_incomplete', None),
    Method(Tracker, 'is_open', 't.is_open', None, boolean=True),
    Method(Tracker, 'get_min_interval', 't.get_min_interval', None),
    Method(Tracker, 'get_scrape_downloaded', 't.get_scrape_downloaded', None),
    Method(Tracker, 'get_group', 't.get_group', None),
    Method(Tracker, 'get_scrape_time_last', 't.get_scrape_time_last', None),
    Method(Tracker, 'get_type', 't.get_type', None),
    Method(Tracker, 'get_normal_interval', 't.get_normal_interval', None),
    Method(Tracker, 'get_url', 't.get_url', None),
    Method(Tracker, 'get_scrape_complete', 't.get_scrape_complete', None),

    # testing
    Method(Tracker, 'fake_method', 't.fake_method', None),

    # MODIFIERS
    Method(Tracker, 'set_enabled', 't.set_enabled', None),
]
