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

import rtorrent.rpc
#from rtorrent.rpc import Method
from rtorrent.peer import Peer
from rtorrent.tracker import Tracker
from rtorrent.file import File

Method = rtorrent.rpc.Method

class Torrent:
    """Represents an individual torrent within a L{RTorrent} instance."""

    def __init__(self, _rt_obj, info_hash, **kwargs):
        self._rt_obj = _rt_obj
        self._p = self._rt_obj._p #: X{ServerProxy} instance
        self.info_hash = info_hash #: info hash for the torrent
        self.rpc_id = self.info_hash #: unique id to pass to rTorrent
        for k in kwargs.keys():
            setattr(self, k, kwargs.get(k, None))

        self.peers = []
        self.trackers = []
        self.files = []

        self._method_list = self._rt_obj._method_dict[self.__class__.__name__]
        rtorrent.rpc._build_rpc_methods(self, self._method_list)
        self._call_custom_methods()

    def __repr__(self):
        return("<Torrent info_hash=\"{0}\">".format(self.info_hash))

    def _call_custom_methods(self):
        self._is_hash_checking_queued()
        self._is_started()
        self._is_paused()

    def get_peers(self):
        """Get list of Peer instances for given torrent.

        @return: L{Peer} instances
        @rtype: list

        @note: also assigns return value to self.peers
        """
        self.peers = []
        #methods = rtorrent.peer.methods
        methods = self._rt_obj._method_dict["Peer"]
        retriever_methods = [m for m in methods if m.is_retriever()]
        # need to leave 2nd arg empty (dunno why)
        m = rtorrent.rpc.Multicall(self._rt_obj)
        m.add("p.multicall", self.info_hash, "",
                *[method.rpc_call + "=" for method in retriever_methods])

        results = m.call()[0] # only sent one call, only need first result

        for result in results:
            results_dict = {}
            # build results_dict
            for m, r in zip(retriever_methods, result):
                results_dict[m.varname] = rtorrent.rpc.process_result(m, r)

            self.peers.append(Peer(self._rt_obj, self.info_hash, **results_dict))

        return(self.peers)

    def get_trackers(self):
        """Get list of Tracker instances for given torrent.

        @return: L{Tracker} instances
        @rtype: list
        
        @note: also assigns return value to self.trackers
        """
        self.trackers = []
        methods = self._rt_obj._method_dict["Tracker"]
        retriever_methods = [m for m in methods if m.is_retriever()]
        # need to leave 2nd arg empty (dunno why)
        m = rtorrent.rpc.Multicall(self._rt_obj)
        m.add("t.multicall", self.info_hash, "",
                *[method.rpc_call + "=" for method in retriever_methods])

        results = m.call()[0] # only sent one call, only need first result

        for result in results:
            results_dict = {}
            # build results_dict
            for m, r in zip(retriever_methods, result):
                results_dict[m.varname] = rtorrent.rpc.process_result(m, r)

            self.trackers.append(Tracker(self._rt_obj, self.info_hash, **results_dict))

        return(self.trackers)

    def get_files(self):
        """Get list of File instances for given torrent.

        @return: L{File} instances
        @rtype: list

        @note: also assigns return value to self.files
        """

        self.files = []
        methods = self._rt_obj._method_dict["File"]
        retriever_methods = [m for m in methods if m.is_retriever()]
        # 2nd arg can be anything, but it'll return all files in torrent regardless
        m = rtorrent.rpc.Multicall(self._rt_obj)
        m.add("f.multicall", self.info_hash, "",
                *[method.rpc_call + "=" for method in retriever_methods])

        results = m.call()[0] # only sent one call, only need first result

        offset_method_index = retriever_methods.index(
                                    rtorrent.rpc.find_method("f.get_offset"))

        # make a list of the offsets of all the files, sort appropriately
        offset_list = sorted([r[offset_method_index] for r in results])

        for result in results:
            results_dict = {}
            # build results_dict
            for m, r in zip(retriever_methods, result):
                results_dict[m.varname] = rtorrent.rpc.process_result(m, r)

            # get proper index positions for each file (based on the file offset)
            f_index = offset_list.index(results_dict["offset"])

            self.files.append(File(self._rt_obj, self.info_hash, \
                                   f_index, **results_dict))

        ### obsolete
        #offsets = sorted([f.offset for f in self.files])
        #for f in self.files:
        #    f.index = offsets.index(f.offset)
        ###

        return(self.files)

    def set_directory(self, d):
        """Modify download directory
        
        @note: Needs to stop torrent in order to change the directory.
        Also doesn't restart after directory is set, that must be called
        separately.
        """
        m = rtorrent.rpc.Multicall(self._rt_obj)
        self.multicall_add(m, "d.try_stop")
        self.multicall_add(m, "d.set_directory", d)

        self.directory = m.call()[-1]

    def start(self):
        """Start the torrent"""
        m = rtorrent.rpc.Multicall(self._rt_obj)
        self.multicall_add(m, "d.try_start")
        self.multicall_add(m, "d.is_active")

        self.active = m.call()[-1]
        return(self.active)

    def stop(self):
        """"Stop the torrent"""
        m = rtorrent.rpc.Multicall(self._rt_obj)
        self.multicall_add(m, "d.try_stop")
        self.multicall_add(m, "d.is_active")

        self.active = m.call()[-1]
        return(self.active)

    def close(self):
        """Close the torrent and it's files"""
        m = rtorrent.rpc.Multicall(self._rt_obj)
        self.multicall_add(m, "d.close")

        return(m.call()[-1])

    def erase(self):
        """Delete the torrent
        
        @note: doesn't delete the downloaded files"""
        m = rtorrent.rpc.Multicall(self._rt_obj)
        self.multicall_add(m, "d.erase")

        return(m.call()[-1])

    def poll(self):
        """poll rTorrent to get latest peer/tracker/file information"""
        self.get_peers()
        self.get_trackers()
        self.get_files()

    def update(self):
        """Refresh torrent data
        
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

        # custom functions (only call private methods, since they only check
        # local variables and are therefore faster)
        self._call_custom_methods()

    def _is_hash_checking_queued(self):
        """Only checks instance variables, shouldn't be called directly"""
        # if hashing == 3, then torrent is marked for hash checking
        # if hash_checking == False, then torrent is waiting to be checked
        self.hash_checking_queued = (self.hashing == 3 and \
                                     self.hash_checking == False)

        return(self.hash_checking_queued)

    ############################################################################
    # CUSTOM METHODS
    ############################################################################

    def is_hash_checking_queued(self):
        """Check if torrent is waiting to be hash checked
        
        @note: Variable where the result for this method is stored Torrent.hash_checking_queued"""
        m = rtorrent.rpc.Multicall(self._rt_obj)
        self.multicall_add(m, "d.get_hashing")
        self.multicall_add(m, "d.is_hash_checking")
        results = m.call()

        # this may be handled by Multicall in the future
        # but for now, just update the variables manually
        setattr(self, "hashing", results[0])
        setattr(self, "hash_checking", results[1])

        return(self._is_hash_checking_queued())

    def _is_paused(self):
        self.paused = (self.state == 0)
        return(self.paused)

    def is_paused(self):
        """Check if torrent is paused
        
        @note: Variable where the result for this method is stored: Torrent.paused"""
        self.get_state()
        return(self._is_paused())

    def _is_started(self):
        self.started = (self.state == 1)
        return(self.started)

    def is_started(self):
        """Check if torrent is started
        
        @note: Variable where the result for this method is stored: Torrent.started"""
        self.get_state()
        return(self._is_started())


methods = [
    # RETRIEVERS
    Method(Torrent, 'is_hash_checked', 'd.is_hash_checked', None, boolean=True),
    Method(Torrent, 'is_hash_checking', 'd.is_hash_checking', None, boolean=True),
    Method(Torrent, 'get_peers_max', 'd.get_peers_max', None),
    Method(Torrent, 'get_tracker_focus', 'd.get_tracker_focus', None),
    Method(Torrent, 'get_skip_total', 'd.get_skip_total', None),
    Method(Torrent, 'get_state', 'd.get_state', None),
    Method(Torrent, 'get_peer_exchange', 'd.get_peer_exchange', None),
    Method(Torrent, 'get_down_rate', 'd.get_down_rate', None),
    Method(Torrent, 'get_connection_seed', 'd.get_connection_seed', None),
    Method(Torrent, 'get_uploads_max', 'd.get_uploads_max', None),
    Method(Torrent, 'get_priority_str', 'd.get_priority_str', None),
    Method(Torrent, 'is_open', 'd.is_open', None, boolean=True),
    Method(Torrent, 'get_peers_min', 'd.get_peers_min', None),
    Method(Torrent, 'get_peers_complete', 'd.get_peers_complete', None),
    Method(Torrent, 'get_tracker_numwant', 'd.get_tracker_numwant', None),
    Method(Torrent, 'get_connection_current', 'd.get_connection_current', None),
    Method(Torrent, 'is_complete', 'd.get_complete', None, boolean=True),
    Method(Torrent, 'get_peers_connected', 'd.get_peers_connected', None),
    Method(Torrent, 'get_chunk_size', 'd.get_chunk_size', None),
    Method(Torrent, 'get_state_counter', 'd.get_state_counter', None),
    Method(Torrent, 'get_base_filename', 'd.get_base_filename', None),
    Method(Torrent, 'get_state_changed', 'd.get_state_changed', None),
    Method(Torrent, 'get_peers_not_connected', 'd.get_peers_not_connected', None),
    Method(Torrent, 'get_directory', 'd.get_directory', None),
    Method(Torrent, 'is_incomplete', 'd.incomplete', None, boolean=True),
    Method(Torrent, 'get_tracker_size', 'd.get_tracker_size', None),
    Method(Torrent, 'is_multi_file', 'd.is_multi_file', None, boolean=True),
    Method(Torrent, 'get_local_id', 'd.get_local_id', None),
    Method(Torrent, 'get_ratio', 'd.get_ratio', None,
           post_process_func=lambda x: x / 1000.0),
    Method(Torrent, 'get_loaded_file', 'd.get_loaded_file', None),
    Method(Torrent, 'get_max_file_size', 'd.get_max_file_size', None),
    Method(Torrent, 'get_size_chunks', 'd.get_size_chunks', None),
    Method(Torrent, 'is_pex_active', 'd.is_pex_active', None, boolean=True),
    Method(Torrent, 'get_hashing', 'd.get_hashing', None),
    Method(Torrent, 'get_bitfield', 'd.get_bitfield', None),
    Method(Torrent, 'get_local_id_html', 'd.get_local_id_html', None),
    Method(Torrent, 'get_connection_leech', 'd.get_connection_leech', None),
    Method(Torrent, 'get_peers_accounted', 'd.get_peers_accounted', None),
    Method(Torrent, 'get_message', 'd.get_message', None),
    Method(Torrent, 'is_active', 'd.is_active', None, boolean=True),
    Method(Torrent, 'get_size_bytes', 'd.get_size_bytes', None),
    Method(Torrent, 'get_ignore_commands', 'd.get_ignore_commands', None),
    Method(Torrent, 'get_creation_date', 'd.get_creation_date', None),
    Method(Torrent, 'get_base_path', 'd.get_base_path', None),
    Method(Torrent, 'get_left_bytes', 'd.get_left_bytes', None),
    Method(Torrent, 'get_size_files', 'd.get_size_files', None),
    Method(Torrent, 'get_size_pex', 'd.get_size_pex', None),
    Method(Torrent, 'is_private', 'd.is_private', None, boolean=True),
    Method(Torrent, 'get_max_size_pex', 'd.get_max_size_pex', None),
    Method(Torrent, 'get_chunks_hashed', 'd.get_chunks_hashed', None),
    Method(Torrent, 'get_priority', 'd.get_priority', None),
    Method(Torrent, 'get_skip_rate', 'd.get_skip_rate', None),
    Method(Torrent, 'get_completed_bytes', 'd.get_completed_bytes', None),
    Method(Torrent, 'get_name', 'd.get_name', None),
    Method(Torrent, 'get_completed_chunks', 'd.get_completed_chunks', None),
    Method(Torrent, 'get_throttle_name', 'd.get_throttle_name', None),
    Method(Torrent, 'get_free_diskspace', 'd.get_free_diskspace', None),
    Method(Torrent, 'get_directory_base', 'd.get_directory_base', None),
    Method(Torrent, 'get_hashing_failed', 'd.get_hashing_failed', None),
    Method(Torrent, 'get_tied_to_file', 'd.get_tied_to_file', None),
    Method(Torrent, 'get_down_total', 'd.get_down_total', None),
    Method(Torrent, 'get_bytes_done', 'd.get_bytes_done', None),
    Method(Torrent, 'get_up_rate', 'd.get_up_rate', None),
    Method(Torrent, 'get_up_total', 'd.get_up_total', None),

    # testing
    Method(Torrent, 'fake_method', 'd.fake_method', None),

    # MODIFIERS
    Method(Torrent, 'set_uploads_max', 'd.set_uploads_max', None),
    Method(Torrent, 'set_tied_to_file', 'd.set_tied_to_file', None),
    Method(Torrent, 'set_tracker_numwant', 'd.set_tracker_numwant', None),
    Method(Torrent, 'set_custom', 'd.set_custom', None),
    Method(Torrent, 'set_priority', 'd.set_priority', None),
    Method(Torrent, 'set_peers_max', 'd.set_peers_max', None),
    Method(Torrent, 'set_hashing_failed', 'd.set_hashing_failed', None),
    Method(Torrent, 'set_message', 'd.set_message', None),
    Method(Torrent, 'set_throttle_name', 'd.set_throttle_name', None),
    Method(Torrent, 'set_peers_min', 'd.set_peers_min', None),
    Method(Torrent, 'set_ignore_commands', 'd.set_ignore_commands', None),
    Method(Torrent, 'set_max_file_size', 'd.set_max_file_size', None),
    Method(Torrent, 'set_custom5', 'd.set_custom5', None),
    Method(Torrent, 'set_custom4', 'd.set_custom4', None),
    Method(Torrent, 'set_custom2', 'd.set_custom2', None),
    Method(Torrent, 'set_custom1', 'd.set_custom1', None),
    Method(Torrent, 'set_custom3', 'd.set_custom3', None),
    Method(Torrent, 'set_connection_current', 'd.set_connection_current', None),
]
