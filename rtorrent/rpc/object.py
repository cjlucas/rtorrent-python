from rtorrent.rpc.method import RPCMethod
from rtorrent.rpc.call import RPCCall
from rtorrent.rpc.caller import RPCCaller


class RPCObject(object):
    _rpc_methods = {}

    @classmethod
    def register_rpc_method(cls, key, rpc_methods, *args, **kwargs):
        cls._rpc_methods[key] = RPCMethod(rpc_methods, *args, **kwargs)

        single_rpc_call = lambda self, *args: self.exec_rpc_call(key, *args)
        setattr(cls, key, single_rpc_call)

    @classmethod
    def get_rpc_methods(cls) -> dict:
        return dict(cls._rpc_methods)

    def __init__(self, context):
        self.context = context

    def rpc_call(self, key, *args) -> RPCCall:
        rpc_method = self._get_rpc_method(key)
        return RPCCall(rpc_method, *args)

    def exec_rpc_call(self, key, *args):
        return RPCCaller(self.context)\
            .add(self.rpc_call(key, *args))\
            .call()[0]

    def _get_rpc_method(self, key) -> RPCMethod:
        # TODO: raise a better exception than KeyError
        rpc_method = self._rpc_methods[key]
        return rpc_method
