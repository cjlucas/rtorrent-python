from rtorrent.rpc.call import RPCCall
from rtorrent.rpc.result import RPCResult
from rtorrent.rpc.method import RPCMethod


import xmlrpc.client

class RPCCaller(object):
    def __init__(self, context):
        self.context = context
        self.calls = []
        self.available_methods = None

    def add(self, method, *args):
        print(method)
        print(args)
        if isinstance(method, RPCMethod):
            call = RPCCall(method, *args)
        elif isinstance(method, str):
            call = RPCCall(RPCMethod(method), *args)
        if hasattr(method, '__self__'):
            call = method.__self__.rpc_call(method.__name__, *args)

        self.calls.append(call)
        return self

    def call(self):
        available_methods = self.context.get_available_rpc_methods()

        multi_call = xmlrpc.client.MultiCall(self.context.get_conn())
        for rpc_call in self.calls:
            method_name = self._get_method_name(rpc_call.get_method())
            rpc_call.do_pre_processing()
            getattr(multi_call, method_name)(*rpc_call.get_args())

        results = []
        for rpc_call, result in zip(self.calls, multi_call()):
            print(rpc_call.get_method().get_method_names())
            result = rpc_call.do_post_processing(result)
            results.append(result)

        return RPCResult(self.calls, results)


    def _get_method_name(self, rpc_method: RPCMethod):
        if self.available_methods is None:
            self.available_methods = self.context.get_available_rpc_methods()

        method_name = rpc_method.get_available_method_name(
            self.available_methods)

        if method_name is None:
            # TODO: Use a different Error subclass
            raise AttributeError("No matches found for {0}".format(
                rpc_method.get_method_names()))

        return method_name
