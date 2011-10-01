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

import re
import sys

_py3 = sys.version_info > (3,)

def int_to_bool(value):
    """Pythonifys boolean values returned by xmlrpc"""
    if value == 1: return(True)
    elif value == 0: return(False)

def bool_to_int(value):
    """Translates python booleans to RPC-safe integers"""
    if value == True: return("1")
    elif value == False: return("0")
    else: return(value)

def cmd_exists(cmds_list, cmd):
    """Check if given command is in list of available commands
    
    @param cmds_list: see L{RTorrent._rpc_methods}
    @type cmds_list: list
    
    @param cmd: name of command to be checked
    @type cmd: str
    
    @return: bool
    """

    return(cmd in cmds_list)

def get_varname(rpc_call):
    """Transform function into variable name.
    
    @note: Example: if the function is p.get_down_rate, the variable name will be
    "down_rate", and the result of the p.get_down_rate= call will be assigned to it.
    """
    # extract variable name from xmlrpc func name
    r = re.search("([ptdf]\.|get\_|is\_|set\_)+([^=]*)", rpc_call, re.I)
    if r: return(r.groups()[-1])
    else: return(None)


def list_to_dict(func_list, results):
    """
    Assign given result to transformed variable name.
        
    @param func_list: list of xmlrpc functions
    @type func_list: list
    
    @param results: results from multicall()
    @type results: list
    
    @return: dict 
             - key: transformed variable 
             - value: corresponding result

    """
    func_dict = {}

    # the order of func_list and results should be in sync
    for i, f in enumerate(func_list):
        # extract variable name from xmlrpc func name
        var_name = get_varname(f)
        if var_name:
            # "is" functions should return True/False, not an int
            if re.search("^[ptdf]\.is_", f, re.I): value = int_to_bool(results[i])
            else: value = results[i]
            func_dict[var_name] = value

    return(func_dict)

def find_torrent(info_hash, torrent_list):
    """Find torrent file in given list of Torrent classes
    
    @param info_hash: info hash of torrent
    @type info_hash: str
    
    @param torrent_list: list of L{Torrent} instances (see L{RTorrent.get_torrents})
    @type torrent_list: list
    
    @return: L{Torrent} instance, or -1 if not found
    """
    for t in torrent_list:
        if t.info_hash == info_hash: return(t)

    return(-1)

def is_valid_port(port):
    """Check if given port is valid"""
    return(0 < int(port) < 65535)
