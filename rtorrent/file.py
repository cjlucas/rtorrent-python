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

class File:
    """Represents an individual file within a L{Torrent} instance."""

    def __init__(self, _p, info_hash, index, **kwargs):
        self._p = _p #: X{ServerProxy} instance
        self.info_hash = info_hash #: info hash for the torrent the file is associated with
        self.index = index #: The position of the file within the file list
        for k in kwargs.keys():
            setattr(self, k, kwargs.get(k, None))

        self.rpc_id = "{0}:f{1}".format(self.info_hash, self.index) #: unique id to pass to rTorrent

    def __repr__(self):
        return("<File index={0} path=\"{1}\">".format(self.index, self.path))

methods = [
    # RETRIEVERS
    Method(File, 'get_last_touched', 'f.get_last_touched', None),
    Method(File, 'get_range_second', 'f.get_range_second', None),
    Method(File, 'get_size_bytes', 'f.get_size_bytes', None),
    Method(File, 'get_priority', 'f.get_priority', None),
    Method(File, 'get_match_depth_next', 'f.get_match_depth_next', None),
    Method(File, 'is_resize_queued', 'f.is_resize_queued', None, boolean=True),
    Method(File, 'get_range_first', 'f.get_range_first', None),
    Method(File, 'get_match_depth_prev', 'f.get_match_depth_prev', None),
    Method(File, 'get_path', 'f.get_path', None),
    Method(File, 'get_completed_chunks', 'f.get_completed_chunks', None),
    Method(File, 'get_path_components', 'f.get_path_components', None),
    Method(File, 'is_created', 'f.is_created', None, boolean=True),
    Method(File, 'is_open', 'f.is_open', None, boolean=True),
    Method(File, 'get_size_chunks', 'f.get_size_chunks', None),
    Method(File, 'get_offset', 'f.get_offset', None),
    Method(File, 'get_frozen_path', 'f.get_frozen_path', None),
    Method(File, 'get_path_depth', 'f.get_path_depth', None),
    Method(File, 'is_create_queued', 'f.is_create_queued', None, boolean=True),

    # MODIFIERS
]
