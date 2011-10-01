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

from rtorrent.common import _py3, cmd_exists, list_to_dict, find_torrent, \
                            is_valid_port, bool_to_int
from rtorrent.file import File
from rtorrent.peer import Peer
from rtorrent.torrent import Torrent
from rtorrent.lib.torrentparser import TorrentParser
from rtorrent.tracker import Tracker
import rtorrent.rpc.methods
import sys
import time
import os.path

if _py3:
    import xmlrpc.client as xmlrpclib #@UnresolvedImport
    from urllib.request import urlopen #@UnresolvedImport
else:
    import xmlrpclib #@UnresolvedImport
    from urllib2 import urlopen #@UnresolvedImport


__version__ = "0.1.0"
__author__ = "Chris Lucas"
__contact__ = "cjlucas07@gmail.com"
__license__ = "MIT"


class RTorrent:
    """ Create a new rTorrent connection """
    def __init__(self, url, _verbose=False):
        self.url = url #: From X{__init__(self, url)}
        self._verbose = _verbose
        self.torrents = [] #: List of L{Torrent} instances
        self.download_list = [] #: List of torrent info hashes
        self._rpc_methods = None #: List of rTorrent RPC methods
        self._p = None #: X{ServerProxy} instance
        self._connected = False

        self._connect()
        if self._connected:
            self._check_commands()
            self.get_client_info()
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

    def _check_commands(self):
        """Check method lists from rtorrent.functions and 
        remove functions that don't exist
        """
        """
        for k in rtorrent.rpc.methods.retrievers:
            rtorrent.rpc.methods.retrievers[k] = \
            [f for f in rtorrent.rpc.methods.retrievers[k]\
              if cmd_exists(self.get_commands(), f)]
        """
        for k in rtorrent.rpc.methods.retrievers.keys():
            # create temp copy to prevent 
            # "dictionary changed size during iteration" error
            temp_dict = dict(rtorrent.rpc.methods.retrievers[k])
            for f in temp_dict:
                rpc_call = temp_dict[f][0]
                if not cmd_exists(self.get_commands(), rpc_call):
                    del rtorrent.rpc.methods.retrievers[k][f]

    def get_commands(self):
        return(self._rpc_methods)

    def get_client_info(self):
        """Get rTorrent client info

        @note: All fields are stored as attributes to self

        @return: None
        """
        GENERAL_FUNCS = rtorrent.rpc.methods.retrievers["general"]
        # create MultiCall object
        multicall = xmlrpclib.MultiCall(self._p)
        for f in GENERAL_FUNCS:
            getattr(multicall, f)()

        results = multicall()
        results = list_to_dict(GENERAL_FUNCS, tuple(results))
        for r in results: setattr(self, r, results[r])

    def get_torrents(self, view="main"):
        """Get list of all torrents in specified view

        @return: list of L{Torrent} instances
        @rtype: list

        @todo: add validity check for specified view
        """
        TORRENT_FUNCS = rtorrent.rpc.methods.retrievers["torrent"]
        results = self._p.d.multicall(view, "d.get_hash=",
                                      *[TORRENT_FUNCS[f][0] + "=" for f in TORRENT_FUNCS])
        self.torrents = []
        self.download_list = []
        for r in results:
            self.download_list.append(r[0])
            self.torrents.append(Torrent(self._p, info_hash=r[0],
                                        **list_to_dict(TORRENT_FUNCS.keys(), r[1:])))

        return(self.torrents)

    def _get_load_function(self, file_type, start, verbose):
        """Determine correct "load torrent" rpc function"""
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


        @note: Because this function includes url verification (if a url was inputted)
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
            self.get_torrents()
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

    def set_check_hash(self, toggle):
        """Enable/Disable hash checking on finished torrents
        
        @param toggle: True to enable, False to disable
        @type toggle: bool
        """
        if value is True: toggle = 1
        else: toggle = 0

        self.check_hash = self._p.set_hash_check(toggle)

    def enable_hash_check(self):
        """Alias for set_hash_check(True)"""
        self.check_hash = self._p.set_hash_check(1)

    def disable_hash_check(self):
        """Alias for set_hash_check(False)"""
        self.hash_check = self._p.set_hash_check(0)

    def poll(self):
        """ poll rTorrent to get latest torrent/peer/tracker/file information 
        
        @note: This will essentially refresh all of the rTorrent data, can be 
        slow if working with a remote rTorrent connection
        
        @return: None
        """
        torrents = self.get_torrents()
        for t in torrents:
            t.get_peers()
            # not finished


def _build_modifier_functions(class_name, dict_key):
    """Build glorified aliases to raw RPC methods"""
    for f in rtorrent.rpc.methods.modifiers[dict_key]:
        rpc_call = rtorrent.rpc.methods.modifiers[dict_key][f][0]
        doc_string = rtorrent.rpc.methods.modifiers[dict_key][f][1]

        if dict_key == "general":
            #caller = lambda self, arg, _fname = rpc_call:\
            #     getattr(self._p, _fname)(bool_to_int(arg))
            caller = lambda self, arg, _fname = rpc_call:\
                rtorrent.rpc.handle_modifier_method(self, _fname,
                                                    bool_to_int(arg))
        elif dict_key == "torrent":
            #caller = lambda self, arg, _fname = rpc_call:\
            #     getattr(self._p, _fname)(self.info_hash, bool_to_int(arg))
            caller = lambda self, arg, _fname = rpc_call:\
                rtorrent.rpc.handle_modifier_method(self, _fname,
                                                    self.info_hash,
                                                    bool_to_int(arg))
        elif dict_key in ["tracker", "file"]:
            #caller = lambda self, arg, _fname = rpc_call:\
            #     getattr(self._p, _fname)(self.info_hash, self.index, bool_to_int(arg))
            caller = lambda self, arg, _fname = rpc_call:\
                 rtorrent.rpc.handle_modifier_method(self, _fname,
                                                     self.info_hash, self.index,
                                                     boot_to_int(arg))

        if doc_string is not None: caller.__doc__ = doc_string
        setattr(class_name, f, caller)

def _build_retriever_functions(class_name, dict_key):
    """Build glorified aliases to raw RPC methods"""
    for f in rtorrent.rpc.methods.retrievers[dict_key]:
        rpc_call = rtorrent.rpc.methods.retrievers[dict_key][f][0]
        doc_string = rtorrent.rpc.methods.retrievers[dict_key][f][1]

        if dict_key == "general":
            caller = lambda self, _fname = rpc_call:\
                rtorrent.rpc.handle_retriever_method(self, _fname)
        elif dict_key == "torrent":
            caller = lambda self, _fname = rpc_call:\
                rtorrent.rpc.handle_retriever_method(self, _fname,
                                                     self.info_hash)
        elif dict_key in ["tracker", "file"]:
            caller = lambda self, _fname = rpc_call:\
                rtorrent.rpc.handle_retriever_method(self, _fname,
                                                     self.info_hash, self.index)

        if doc_string is not None: caller.__doc__ = doc_string
        setattr(class_name, f, caller)

for c in ((RTorrent, "general"), (Torrent, "torrent"),
          (Tracker, "tracker"), (File, "file")):
    # TODO: add support for File and Peer functions
    _build_modifier_functions(c[0], c[1])
    _build_retriever_functions(c[0], c[1])
