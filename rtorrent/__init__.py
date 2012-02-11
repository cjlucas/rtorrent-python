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

from rtorrent.common import _py3, cmd_exists, find_torrent, \
    is_valid_port, bool_to_int, convert_version_tuple_to_str
from rtorrent.lib.torrentparser import TorrentParser
from rtorrent.rpc import Method
from rtorrent.torrent import Torrent
import os.path
import rtorrent.rpc #@UnresolvedImport
import sys
import time


if _py3:
    import xmlrpc.client as xmlrpclib #@UnresolvedImport
    from urllib.request import urlopen #@UnresolvedImport
else:
    import xmlrpclib #@UnresolvedImport @Reimport
    from urllib2 import urlopen #@UnresolvedImport @Reimport


__version__ = "0.2.6"
__author__ = "Chris Lucas"
__contact__ = "chris@chrisjlucas.com"
__license__ = "MIT"

MIN_RTORRENT_VERSION = (0, 8, 1)
MIN_RTORRENT_VERSION_STR = convert_version_tuple_to_str(MIN_RTORRENT_VERSION)


class RTorrent:
    """ Create a new rTorrent connection """
    rpc_prefix = None

    def __init__(self, url, _verbose=False):
        self.url = url #: From X{__init__(self, url)}
        self._verbose = _verbose
        self.torrents = [] #: List of L{Torrent} instances
        self.download_list = [] #: List of torrent info hashes
        self._rpc_methods = [] #: List of rTorrent RPC methods
        self._p = None #: X{ServerProxy} instance
        self._connected = False
        self._torrent_cache = []

        self._connect()
        if self._connected:
            self.client_version_tuple = tuple([int(i) for i in \
                        self._p.system.client_version().split(".")])

            self._build_method_dict()
            self._method_list = self._method_dict[self.__class__.__name__]
            rtorrent.rpc._build_rpc_methods(self, self._method_list)

            self.update()
            assert self._meets_version_requirement() is True, \
                "Error: Minimum rTorrent version required is {0}".format(
                                                    MIN_RTORRENT_VERSION_STR)
            self.get_torrents()

    def _connect(self):
        """Create rTorrent connection"""
        self._connected = False
        self._p = xmlrpclib.ServerProxy(self.url, verbose=self._verbose)

        try:
            # will fail if url given is invalid
            self._rpc_methods = self._p.system.listMethods()
            self._connected = True
        except xmlrpclib.ProtocolError as err:
            sys.stderr.write("*** Exception caught: ProtocolError")
            sys.stderr.write("URL: {0}".format(err.url))
            sys.stderr.write("Error code: {0}".format(err.errcode))
            sys.stderr.write("Error message: {0}".format(err.errmsg))
        except xmlrpclib.ResponseError:
            sys.stderr.write("*** Exception caught: ResponseError")

    def _build_method_dict(self):
        self._method_dict = {}
        for method_list in _all_methods_list:
            for m in method_list:
                if m.is_available(self):
                    if m.class_name not in self._method_dict.keys():
                        self._method_dict[m.class_name] = []
                    self._method_dict[m.class_name].append(m)

    def _meets_version_requirement(self):
        """Check if rTorrent version is meets requirements"""
        if hasattr(self, "client_version_tuple"):
            return(self.client_version_tuple >= MIN_RTORRENT_VERSION)
        else:
            return(False)

    def get_rpc_methods(self):
        """Get list of raw RPC commands supported by rTorrent
        
        @return: raw RPC commands
        @rtype: list
        """
        return(self._rpc_methods)

    def get_torrents(self, view="main"):
        """Get list of all torrents in specified view

        @return: list of L{Torrent} instances
        @rtype: list

        @todo: add validity check for specified view
        """
        self.torrents = []
        self.download_list = []
        methods = rtorrent.torrent.methods
        retriever_methods = [m for m in methods \
                             if m.is_retriever() and m.is_available(self)]

        m = rtorrent.rpc.Multicall(self)
        m.add("d.multicall", view, "d.get_hash=",
                *[method.rpc_call + "=" for method in retriever_methods])

        results = m.call()[0] # only sent one call, only need first result

        for result in results:
            results_dict = {}
            # build results_dict
            for m, r in zip(retriever_methods, result[1:]): # result[0] is the info_hash
                results_dict[m.varname] = rtorrent.rpc.process_result(m, r)

            self.download_list.append(result[0])
            self.torrents.append(
                    Torrent(self, info_hash=result[0], **results_dict)
            )

        self._manage_torrent_cache()
        return(self.torrents)

    def _manage_torrent_cache(self):
        """Carry tracker/peer/file lists over to new torrent list"""
        for torrent in self._torrent_cache:
            new_torrent = rtorrent.common.find_torrent(torrent.info_hash,
                                                       self.torrents)
            if new_torrent != -1:
                new_torrent.files = torrent.files
                new_torrent.peers = torrent.peers
                new_torrent.trackers = torrent.trackers

        self._torrent_cache = self.torrents

    def _get_load_function(self, file_type, start, verbose):
        """Determine correct "load torrent" RPC method"""
        func_name = None
        if file_type == "url":
            # url strings can be input directly
            if start and verbose:   func_name = "load_start_verbose"
            elif start:             func_name = "load_start"
            elif verbose:           func_name = "load_verbose"
            else:                   func_name = "load"
        elif file_type in ["file", "raw"]:
            if start and verbose:   func_name = "load_raw_start_verbose"
            elif start:             func_name = "load_raw_start"
            elif verbose:           func_name = "load_raw_verbose"
            else:                   func_name = "load_raw"

        return(func_name)

    def load_torrent(self, torrent, start=False, verbose=False, verify_load=True):
        """
        Loads torrent into rTorrent (with various enhancements)

        @param torrent: can be a url, a path to a local file, or the raw data
        of a torrent file
        @type torrent: str

        @param start: start torrent when loaded
        @type start: bool

        @param verbose: print error messages to rTorrent log
        @type verbose: bool

        @param verify_load: verify that torrent was added to rTorrent successfully
        @type verify_load: bool

        @return: Depends on verify_load:
                 - if verify_load is True, (and the torrent was 
                 loaded successfully), it'll return a L{Torrent} instance
                 - if verify_load is False, it'll return None

        @rtype: L{Torrent} instance or None

        @raise AssertionError: If the torrent wasn't successfully added to rTorrent
                               - Check L{TorrentParser} for the AssertionError's
                               it raises


        @note: Because this function includes url verification (if a url was input)
        as well as verification as to whether the torrent was successfully added,
        this function doesn't execute instantaneously. If that's what you're
        looking for, use load_torrent_simple() instead.
        """
        tp = TorrentParser(torrent)
        torrent = xmlrpclib.Binary(tp._raw_torrent)
        info_hash = tp.info_hash

        func_name = self._get_load_function("raw", start, verbose)

        # load torrent
        getattr(self._p, func_name)(torrent)

        if verify_load:
            MAX_RETRIES = 3
            i = 0
            while i < MAX_RETRIES:
                self.get_torrents()
                if info_hash in self.download_list: break

                time.sleep(1) # was still getting AssertionErrors, delay should help
                i += 1

            assert info_hash in self.download_list, "Adding torrent was unsuccessful."

        return(find_torrent(info_hash, self.torrents))

    def load_torrent_simple(self, torrent, file_type,
                            start=False, verbose=False):
        """Loads torrent into rTorrent
        
        @param torrent: can be a url, a path to a local file, or the raw data
        of a torrent file
        @type torrent: str
        
        @param file_type: valid options: "url", "file", or "raw"
        @type file_type: str
        
        @param start: start torrent when loaded
        @type start: bool
                
        @param verbose: print error messages to rTorrent log
        @type verbose: bool
    
        @return: None
        
        @raise AssertionError: if incorrect file_type is specified
        
        @note: This function was written for speed, it includes no enhancements.
        If you input a url, it won't check if it's valid. You also can't get 
        verification that the torrent was successfully added to rTorrent. 
        Use load_torrent() if you would like these features.
        """

        assert file_type in ["raw", "file", "url"], \
            "Invalid file_type, options are: 'url', 'file', 'raw'."
        func_name = self._get_load_function(file_type, start, verbose)

        if file_type == "file":
            # since we have to assume we're connected to a remote rTorrent
            # client, we have to read the file and send it to rT as raw
            assert os.path.isfile(torrent), \
                "Invalid path: \"{0}\"".format(torrent)
            torrent = open(torrent, "rb").read()

        if file_type in ["raw", "file"]:    finput = xmlrpclib.Binary(torrent)
        elif file_type == "url":            finput = torrent

        getattr(self._p, func_name)(finput)

    def set_dht_port(self, port):
        """Set DHT port
        
        @param port: port
        @type port: int
        
        @raise AssertionError: if invalid port is given
        """
        assert is_valid_port(port), "Valid port range is 0-65535"
        self.dht_port = self._p.set_dht_port(port)

    def enable_check_hash(self):
        """Alias for set_check_hash(True)"""
        self.set_check_hash(True)

    def disable_check_hash(self):
        """Alias for set_check_hash(False)"""
        self.set_check_hash(False)

    def poll(self):
        """ poll rTorrent to get latest torrent/peer/tracker/file information 
        
        @note: This essentially refreshes every aspect of the rTorrent
        connection, so it can be very slow if working with a remote 
        connection that has a lot of torrents loaded.
        
        @return: None
        """
        self.update()
        torrents = self.get_torrents()
        for t in torrents:
            t.poll()

    def update(self):
        """Refresh rTorrent client info

        @note: All fields are stored as attributes to self.

        @return: None
        """
        multicall = rtorrent.rpc.Multicall(self)
        retriever_methods = [m for m in self._method_list \
                        if m.is_retriever() and m.is_available(self)]
        for method in retriever_methods:
            multicall.add(method)

        result = multicall.call()
        for m, r in zip(retriever_methods, result):
            setattr(self, m.varname, rtorrent.rpc.process_result(m, r))

def _build_class_methods(class_obj):
    # multicall add class
    caller = lambda self, multicall, method, *args:\
        multicall.add(method, self.rpc_id, *args)

    caller.__doc__ = """Same as Multicall.add(), but with automatic inclusion
                        of the rpc_id
                        
                        @param multicall: A L{Multicall} instance
                        @type: multicall: Multicall
                        
                        @param method: L{Method} instance or raw rpc method
                        @type: Method or str
                        
                        @param args: optional arguments to pass
                        """
    setattr(class_obj, "multicall_add", caller)

methods = [
    # RETRIEVERS
    Method(RTorrent, 'get_xmlrpc_size_limit', 'get_xmlrpc_size_limit', None),
    Method(RTorrent, 'get_proxy_address', 'get_proxy_address', None),
    Method(RTorrent, 'get_split_suffix', 'get_split_suffix', None),
    Method(RTorrent, 'get_up_limit', 'get_upload_rate', None),
    Method(RTorrent, 'get_max_memory_usage', 'get_max_memory_usage', None),
    Method(RTorrent, 'get_max_open_files', 'get_max_open_files', None),
    Method(RTorrent, 'get_min_peers_seed', 'get_min_peers_seed', None),
    Method(RTorrent, 'get_use_udp_trackers', 'get_use_udp_trackers', None),
    Method(RTorrent, 'get_preload_min_size', 'get_preload_min_size', None),
    Method(RTorrent, 'get_max_uploads', 'get_max_uploads', None),
    Method(RTorrent, 'get_max_peers', 'get_max_peers', None),
    Method(RTorrent, 'get_timeout_sync', 'get_timeout_sync', None),
    Method(RTorrent, 'get_receive_buffer_size', 'get_receive_buffer_size', None),
    Method(RTorrent, 'get_split_file_size', 'get_split_file_size', None),
    Method(RTorrent, 'get_dht_throttle', 'get_dht_throttle', None),
    Method(RTorrent, 'get_max_peers_seed', 'get_max_peers_seed', None),
    Method(RTorrent, 'get_min_peers', 'get_min_peers', None),
    Method(RTorrent, 'get_tracker_numwant', 'get_tracker_numwant', None),
    Method(RTorrent, 'get_max_open_sockets', 'get_max_open_sockets', None),
    Method(RTorrent, 'get_session', 'get_session', None),
    Method(RTorrent, 'get_ip', 'get_ip', None),
    Method(RTorrent, 'get_scgi_dont_route', 'get_scgi_dont_route', None),
    Method(RTorrent, 'get_hash_read_ahead', 'get_hash_read_ahead', None),
    Method(RTorrent, 'get_http_cacert', 'get_http_cacert', None),
    Method(RTorrent, 'get_dht_port', 'get_dht_port', None),
    Method(RTorrent, 'get_handshake_log', 'get_handshake_log', None),
    Method(RTorrent, 'get_preload_type', 'get_preload_type', None),
    Method(RTorrent, 'get_max_open_http', 'get_max_open_http', None),
    Method(RTorrent, 'get_http_capath', 'get_http_capath', None),
    Method(RTorrent, 'get_max_downloads_global', 'get_max_downloads_global', None),
    Method(RTorrent, 'get_name', 'get_name', None),
    Method(RTorrent, 'get_session_on_completion', 'get_session_on_completion', None),
    Method(RTorrent, 'get_down_limit', 'get_download_rate', None),
    Method(RTorrent, 'get_down_total', 'get_down_total', None),
    Method(RTorrent, 'get_up_rate', 'get_up_rate', None),
    Method(RTorrent, 'get_hash_max_tries', 'get_hash_max_tries', None),
    Method(RTorrent, 'get_peer_exchange', 'get_peer_exchange', None),
    Method(RTorrent, 'get_down_rate', 'get_down_rate', None),
    Method(RTorrent, 'get_connection_seed', 'get_connection_seed', None),
    Method(RTorrent, 'get_http_proxy', 'get_http_proxy', None),
    Method(RTorrent, 'get_stats_preloaded', 'get_stats_preloaded', None),
    Method(RTorrent, 'get_timeout_safe_sync', 'get_timeout_safe_sync', None),
    Method(RTorrent, 'get_hash_interval', 'get_hash_interval', None),
    Method(RTorrent, 'get_port_random', 'get_port_random', None),
    Method(RTorrent, 'get_directory', 'get_directory', None),
    Method(RTorrent, 'get_port_open', 'get_port_open', None),
    Method(RTorrent, 'get_max_file_size', 'get_max_file_size', None),
    Method(RTorrent, 'get_stats_not_preloaded', 'get_stats_not_preloaded', None),
    Method(RTorrent, 'get_memory_usage', 'get_memory_usage', None),
    Method(RTorrent, 'get_connection_leech', 'get_connection_leech', None),
    Method(RTorrent, 'get_check_hash', 'get_check_hash', None, boolean=True),
    Method(RTorrent, 'get_session_lock', 'get_session_lock', None),
    Method(RTorrent, 'get_preload_required_rate', 'get_preload_required_rate', None),
    Method(RTorrent, 'get_max_uploads_global', 'get_max_uploads_global', None),
    Method(RTorrent, 'get_send_buffer_size', 'get_send_buffer_size', None),
    Method(RTorrent, 'get_port_range', 'get_port_range', None),
    Method(RTorrent, 'get_max_downloads_div', 'get_max_downloads_div', None),
    Method(RTorrent, 'get_max_uploads_div', 'get_max_uploads_div', None),
    Method(RTorrent, 'get_safe_sync', 'get_safe_sync', None),
   #Method(RTorrent, 'get_log.tracker', 'get_log.tracker', None),
    Method(RTorrent, 'get_bind', 'get_bind', None),
    Method(RTorrent, 'get_up_total', 'get_up_total', None),
    Method(RTorrent, 'get_client_version', 'system.client_version', None),
    Method(RTorrent, 'get_library_version', 'system.library_version', None),

    # MODIFIERS
    Method(RTorrent, 'set_http_proxy', 'set_http_proxy', None),
    Method(RTorrent, 'set_max_memory_usage', 'set_max_memory_usage', None),
    Method(RTorrent, 'set_max_file_size', 'set_max_file_size', None),
    Method(RTorrent, 'set_bind', 'set_bind',
           """Set address bind
           
           @param arg: ip address
           @type arg: str
           """),
    Method(RTorrent, 'set_up_limit', 'set_upload_rate',
           """Set global upload limit (in bytes)
           
           @param arg: speed limit
           @type arg: int
           """),
    Method(RTorrent, 'set_port_random', 'set_port_random', None),
    Method(RTorrent, 'set_connection_leech', 'set_connection_leech', None),
    Method(RTorrent, 'set_tracker_numwant', 'set_tracker_numwant', None),
    Method(RTorrent, 'set_max_peers', 'set_max_peers', None),
    Method(RTorrent, 'set_min_peers', 'set_min_peers', None),
    Method(RTorrent, 'set_max_uploads_div', 'set_max_uploads_div', None),
    Method(RTorrent, 'set_max_open_files', 'set_max_open_files', None),
    Method(RTorrent, 'set_max_downloads_global', 'set_max_downloads_global', None),
    Method(RTorrent, 'set_session_lock', 'set_session_lock', None),
    Method(RTorrent, 'set_session', 'set_session', None),
    Method(RTorrent, 'set_split_suffix', 'set_split_suffix', None),
    Method(RTorrent, 'set_hash_interval', 'set_hash_interval', None),
    Method(RTorrent, 'set_handshake_log', 'set_handshake_log', None),
    Method(RTorrent, 'set_port_range', 'set_port_range', None),
    Method(RTorrent, 'set_min_peers_seed', 'set_min_peers_seed', None),
    Method(RTorrent, 'set_scgi_dont_route', 'set_scgi_dont_route', None),
    Method(RTorrent, 'set_preload_min_size', 'set_preload_min_size', None),
    Method(RTorrent, 'set_log.tracker', 'set_log.tracker', None),
    Method(RTorrent, 'set_max_uploads_global', 'set_max_uploads_global', None),
    Method(RTorrent, 'set_down_limit', 'set_download_rate',
           """Set global download limit (in bytes)
           
           @param arg: speed limit
           @type arg: int
           """),
    Method(RTorrent, 'set_preload_required_rate', 'set_preload_required_rate', None),
    Method(RTorrent, 'set_hash_read_ahead', 'set_hash_read_ahead', None),
    Method(RTorrent, 'set_max_peers_seed', 'set_max_peers_seed', None),
    Method(RTorrent, 'set_max_uploads', 'set_max_uploads', None),
    Method(RTorrent, 'set_session_on_completion', 'set_session_on_completion', None),
    Method(RTorrent, 'set_max_open_http', 'set_max_open_http', None),
    Method(RTorrent, 'set_directory', 'set_directory', None),
    Method(RTorrent, 'set_http_cacert', 'set_http_cacert', None),
    Method(RTorrent, 'set_dht_throttle', 'set_dht_throttle', None),
    Method(RTorrent, 'set_hash_max_tries', 'set_hash_max_tries', None),
    Method(RTorrent, 'set_proxy_address', 'set_proxy_address', None),
    Method(RTorrent, 'set_split_file_size', 'set_split_file_size', None),
    Method(RTorrent, 'set_receive_buffer_size', 'set_receive_buffer_size', None),
    Method(RTorrent, 'set_use_udp_trackers', 'set_use_udp_trackers', None),
    Method(RTorrent, 'set_connection_seed', 'set_connection_seed', None),
    Method(RTorrent, 'set_xmlrpc_size_limit', 'set_xmlrpc_size_limit', None),
    Method(RTorrent, 'set_xmlrpc_dialect', 'set_xmlrpc_dialect', None),
    Method(RTorrent, 'set_safe_sync', 'set_safe_sync', None),
    Method(RTorrent, 'set_http_capath', 'set_http_capath', None),
    Method(RTorrent, 'set_send_buffer_size', 'set_send_buffer_size', None),
    Method(RTorrent, 'set_max_downloads_div', 'set_max_downloads_div', None),
    Method(RTorrent, 'set_name', 'set_name', None),
    Method(RTorrent, 'set_port_open', 'set_port_open', None),
    Method(RTorrent, 'set_timeout_sync', 'set_timeout_sync', None),
    Method(RTorrent, 'set_peer_exchange', 'set_peer_exchange', None),
    Method(RTorrent, 'set_ip', 'set_ip',
           """Set IP
           
           @param arg: ip address
           @type arg: str
           """),
    Method(RTorrent, 'set_timeout_safe_sync', 'set_timeout_safe_sync', None),
    Method(RTorrent, 'set_preload_type', 'set_preload_type', None),
    Method(RTorrent, 'set_check_hash', 'set_check_hash',
           """Enable/Disable hash checking on finished torrents
        
            @param arg: True to enable, False to disable
            @type arg: bool
            """, boolean=True),
    # just testing
    Method(RTorrent, 'fake_method', 'get_fake_method', None),
    Method(RTorrent, 'fake_method_dos', 'get_fake_method_dos', None,
           min_version=(9, 9, 9)),
]

_all_methods_list = [methods,
                    rtorrent.file.methods,
                    rtorrent.torrent.methods,
                    rtorrent.tracker.methods,
                    rtorrent.peer.methods,
]

for c in [rtorrent.file.File,
          rtorrent.torrent.Torrent,
          rtorrent.tracker.Tracker,
          rtorrent.peer.Peer]:
    _build_class_methods(c)
