# Copyright (c) 2011 Chris Lucas, <cjlucas07@gmail.com>
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

from rtorrent.rpc import Method
import rtorrent.rpc

class Tracker:
    """Represents an individual tracker within a L{Torrent} instance."""

    def __init__(self, _p, info_hash, **kwargs):
        self._p = _p #: X{ServerProxy} instance
        self.info_hash = info_hash #: info hash for the torrent using this tracker
        for k in kwargs.keys():
            setattr(self, k, kwargs.get(k, None))

        # for clarity's sake...
        self.index = self.group #: position of tracker within the torrent's tracker list
        self.rpc_id = "{0}:t{1}".format(self.info_hash, self.index) #: unique id to pass to rTorrent

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
        multicall = rtorrent.rpc.Multicall(self._p)
        retriever_methods = [m for m in methods if m.is_retriever()]
        for method in retriever_methods:
            multicall.add(method, "{0}:t{1}".format(self.info_hash, self.index))

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

    # MODIFIERS
    Method(Tracker, 'set_enabled', 't.set_enabled', None),
]
