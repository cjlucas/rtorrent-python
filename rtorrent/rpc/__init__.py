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

import rtorrent
import re
from rtorrent.common import _py3, bool_to_int
from rtorrent.err import RTorrentVersionError, MethodError

if _py3: import xmlrpc.client as xmlrpclib #@UnresolvedImport
else: import xmlrpclib #@UnresolvedImport @Reimport

def get_varname(rpc_call):
    """Transform rpc method into variable name.
    
    @newfield example: Example
    @example: if the name of the rpc method is 'p.get_down_rate', the variable
    name will be 'down_rate'
    """
    # extract variable name from xmlrpc func name
    r = re.search("([ptdf]\.|system\.|get\_|is\_|set\_)+([^=]*)", rpc_call, re.I)
    if r: return(r.groups()[-1])
    else: return(None)

class DummyClass:
    def __init__(self):
        pass

class Method:
    """Represents an individual RPC method"""

    def __init__(self, _class, method_name,
                 rpc_call, docstring=None, varname=None,
                 min_version=(0, 0, 0), **kwargs):
        self._class = _class #: Class this method is associated with
        self.class_name = _class.__name__
        self.method_name = method_name #: name of public-facing method
        self.rpc_call = rpc_call #: name of rpc method
        self.docstring = docstring #: docstring for rpc method (optional)
        self.varname = varname #: variable for the result of the method call, usually set to self.varname
        self.min_version = min_version #: Minimum version of rTorrent required
        self.boolean = kwargs.get("boolean", False) #: returns boolean value?
        self.post_process_func = kwargs.get("post_process_func", None) #: custom post process function
        self.required_args = [] #: Arguments required when calling the method (not utilized)

        self.method_type = self._get_method_type()

        if self.varname is None: self.varname = get_varname(self.rpc_call)
        assert self.varname is not None, "Couldn't get variable name."

    def __repr__(self):
        return("<Method method_name='{0}', rpc_call='{1}'>".format(
                                                            self.method_name,
                                                            self.rpc_call))

    def _get_method_type(self):
        """Determine whether method is a modifier or a retriever"""
        if self.method_name[:4] == "set_": return('m') # modifier
        else: return('r') # retriever

    def is_modifier(self):
        if self.method_type == 'm': return(True)
        else: return(False)

    def is_retriever(self):
        if self.method_type == 'r': return(True)
        else: return(False)

    def is_available(self, rt_obj):
        if rt_obj.client_version_tuple < self.min_version or \
                self.rpc_call not in rt_obj._rpc_methods:
            return(False)
        else:
            return(True)

class Multicall:
    def __init__(self, rt_obj, **kwargs):
        self.rt_obj = rt_obj #: X{RTorrent} instance
        self._proxy = self.rt_obj._p
        #self.info_hash = kwargs.get("info_hash", None)
        #self.index = kwargs.get("index", None)
        self.calls = []

    def add(self, method, *args):
        """Add call to multicall
        
        @param method: L{Method} instance or name of raw RPC method
        @type method: Method or str
        
        @param args: call arguments
        """
        # if a raw rpc method was given instead of a Method instance,
        # try and find the instance for it. And if all else fails, create a
        # dummy Method instance
        if isinstance(method, str):
            result = find_method(method)
            # if result not found
            if result == -1:
                method = Method(DummyClass, method, method)
            else:
                method = result

        # ensure method is available before adding
        assert method.is_available(self.rt_obj), "Method unavailable."

        self.calls.append((method, args))

    def list_calls(self):
        for c in self.calls: print(c)

    def call(self):
        """Execute added multicall calls
        
        @return: the results (post-processing), in the order they were added
        @rtype: tuple
        """
        m = xmlrpclib.MultiCall(self._proxy)
        for call in self.calls:
            method, args = call
            rpc_call = getattr(method, "rpc_call")
            getattr(m, rpc_call)(*args)

        results = m()
        results = tuple(results)
        results_processed = []

        for r, c in zip(results, self.calls):
            method = c[0]
            results_processed.append(process_result(method, r))

        return(tuple(results_processed))

def call_method(class_obj, method, *args):
    """Handles single RPC call and assigns result to varname
    
    @param class_obj: Peer/File/Torrent/Tracker/RTorrent instance
    @type class_obj: object
    
    @param method: L{Method} instance or name of raw RPC method
    @type method: Method or str
    """
    if method.is_retriever(): args = args[:-1]
    else: assert args[-1] is not None, "No argument given."

    rpc_call = method.rpc_call
    if class_obj.__class__.__name__ == "RTorrent": rt_obj = class_obj
    else: rt_obj = class_obj._rt_obj

    # check if rpc method is even available
    if rpc_call not in rt_obj._rpc_methods:
        # check if rTorrent meets minimum version requirement of the method
        if rt_obj.client_version_tuple < method.min_version:
            raise RTorrentVersionError(method.min_version,
                                       rt_obj.client_version_tuple)
        else:
            raise MethodError("RPC method '{0}' not found.".format(rpc_call))

    m = Multicall(rt_obj)
    m.add(method, *args)
    # only added one method, only getting one result back
    ret_value = m.call()[0]

    if method.is_retriever():
        #value = process_result(method, ret_value)
        value = ret_value #MultiCall already processed the result
    else:
        # we're setting the user's input to method.varname
        # but we'll return the value that xmlrpc gives us
        value = process_result(method, args[-1])

    setattr(class_obj, method.varname, value)
    return(ret_value)


def find_method(rpc_call):
    """Return L{Method} instance associated with given RPC call"""
    method_lists = [
                    rtorrent.methods,
                    rtorrent.file.methods,
                    rtorrent.tracker.methods,
                    rtorrent.peer.methods,
                    rtorrent.torrent.methods,
    ]

    for l in method_lists:
        for m in l:
            if m.rpc_call.lower() == rpc_call.lower(): return(m)

    return(-1)

def process_result(method, result):
    """Process given C{B{result}} based on flags set in C{B{method}}
    
    @param method: L{Method} instance
    @type method: Method
    
    @param result: result to be processed (the result of given L{Method} instance)
    
    @note: Supported Processing:
        - boolean - convert ones and zeros returned by rTorrent and 
        convert to python boolean values
    """
    # handle custom post processing function
    if method.post_process_func is not None:
        result = method.post_process_func(result)

    # is boolean?
    if method.boolean:
        if result in [1, '1']: result = True
        elif result in [0, '0']: result = False

    return(result)

def _build_rpc_methods(class_obj, method_list):
    """Build glorified aliases to raw RPC methods"""
    for m in method_list:
        class_name = m.class_name
        if class_name != class_obj.__class__.__name__: continue

        if class_name == "RTorrent":
            caller = lambda arg = None, self = class_obj, method = m:\
                call_method(self, method, bool_to_int(arg))
        elif class_name == "Torrent":
            caller = lambda arg = None, self = class_obj, method = m:\
                call_method(self, method, self.rpc_id,
                                         bool_to_int(arg))
        elif class_name in ["Tracker", "File"]:
            caller = lambda arg = None, self = class_obj, method = m:\
                call_method(self, method, self.rpc_id,
                                         bool_to_int(arg))

        elif class_name == "Peer":
            caller = lambda arg = None, self = class_obj, method = m:\
                call_method(self, method, self.rpc_id,
                                         bool_to_int(arg))

        if m.docstring is not None: caller.__doc__ = m.docstring

        setattr(class_obj, m.method_name, caller)

