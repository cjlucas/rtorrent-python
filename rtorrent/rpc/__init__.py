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
from rtorrent.common import *

def is_bool(call_type, rpc_call):
    assert call_type in rtorrent.rpc.methods.retrievers.keys()
    func_dict = rtorrent.rpc.methods.retrievers[call_type]
    # get a dict of rpc functions that have a boolean value set (hackish)
    bool_funcs = {func_dict[f][0]:func_dict[f][-1] \
                  for f in func_dict.keys() if len(func_dict[f]) > 2}

    if rpc_call in bool_funcs.keys() and bool_funcs[rpc_call] == True:
        return(True)
    else:
        return(False)

def handle_modifier_method(self, rpc_call, *args):
    """Handles RPC modifier methods
    
    @param rpc_call: name of the raw RPC method
    @type rpc_call: string
    
    @param args: depends on the rpc_call
    @type args: string or int
    """
    getattr(self._p, rpc_call)(*args)
    var_name = get_varname(rpc_call)
    if var_name is not None: setattr(self, var_name, args[-1])

def handle_retriever_method(self, rpc_call, *args):
    """Handles RPC retrieval methods
    
    @param rpc_call: name of the raw RPC method
    @type rpc_call: string
    
    @param args: depends on the rpc_call
    @type args: string or int
    
    @return: value that was intended to be retrieved
    @rtype: string or int
    """
    ret_value = getattr(self._p, rpc_call)(*args)
    var_name = get_varname(rpc_call)
    if var_name is not None: setattr(self, var_name, ret_value)
    return(ret_value)
