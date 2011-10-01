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

import rtorrent.rpc.methods
from rtorrent.peer import Peer
from rtorrent.tracker import Tracker
from rtorrent.file import File
from rtorrent.common import list_to_dict

class Torrent:
    """Represents an individual torrent within a L{RTorrent} instance."""
    def __init__(self, _p, info_hash, **kwargs):
        self._p = _p #: X{ServerProxy} instance
        self.info_hash = info_hash #: info hash for the torrent
        for k in kwargs.keys():
            setattr(self, k, kwargs.get(k, None))
        self.peers = []
        self.trackers = []
        self.files = []
        #setattr(self, "get_priority_str", lambda : eval("_p.d.get_priority_str(self._info_hash)"))


    def __repr__(self):
        return("<Torrent info_hash=\"{0}\">".format(self.info_hash))

    def get_peers(self):
        """Get list of Peer instances for given torrent.
        
        @return: L{Peer} instances
        @rtype: list
        
        @note: also assigns return value to self.peers
        """
        self.peers = []
        PEER_FUNCS = rtorrent.rpc.methods.retrievers["peer"]
        # need to leave 2nd arg empty for peer range (not yet implemented)
        peer_list = self._p.p.multicall(self.info_hash, "",
                                *[PEER_FUNCS[f][0] + "=" for f in PEER_FUNCS])
        for p in peer_list:
            self.peers.append(Peer(self._p, **list_to_dict(PEER_FUNCS.keys(), p)))

        return(self.peers)

    def get_trackers(self):
        """Get list of Tracker instances for given torrent.
        
        @return: L{Tracker} instances
        @rtype: list
       
        @note: also assigns return value to self.trackers
        """
        self.trackers = []
        TRACKER_FUNCS = rtorrent.rpc.methods.retrievers["tracker"]
        # need to leave 2nd arg empty (dunno why)
        tracker_list = self._p.t.multicall(self.info_hash, "",
                            *[TRACKER_FUNCS[f][0] + "=" for f in TRACKER_FUNCS])
        for t in tracker_list:
            self.trackers.append(
                Tracker(self._p, self.info_hash,
                         **list_to_dict(TRACKER_FUNCS.keys(), t))
            )

        return(self.trackers)

    def get_files(self):
        """Get list of File instances for given torrent.
        
        @return: L{File} instances
        @rtype: list
       
        @note: also assigns return value to self.files
        """
        self.files = []
        FILE_FUNCS = rtorrent.rpc.methods.retrievers["file"]
        # 2nd arg can be anything, but it'll return all files in torrent regardless
        file_list = self._p.f.multicall(self.info_hash, "",
                                *[FILE_FUNCS[f][0] + "=" for f in FILE_FUNCS])
        for f in file_list:
            self.files.append(
                File(self._p, self.info_hash, **list_to_dict(FILE_FUNCS.keys(), f))
            )

        # add proper index positions for each file (based on the file offset)
        offsets = sorted([f.offset for f in self.files])
        for f in self.files:
            f.index = offsets.index(f.offset)

        return(self.files)

    def set_directory(self, d):
        """Modify download directory"""
        self._p.d.try_stop(self.info_hash)
        self._p.d.set_directory(self.info_hash, d)
        #self._p.d.try_start(self.info_hash)

    def start(self):
        """Start the torrent"""
        self._p.d.try_start(self.info_hash)

    def stop(self):
        """"Stop the torrent"""
        self.p.d.try_stop(self.info_hash)

    def poll(self):
        """poll rTorrent to get latest peer/tracker/file information"""
        self.get_peers()
        self.get_trackers()
        self.get_files()
