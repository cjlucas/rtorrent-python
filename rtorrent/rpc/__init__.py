from rtorrent.rpc.method import RPCMethod
from rtorrent.context import RTContext
from rtorrent.rpc.call import RPCCall
from rtorrent.rpc.caller import RPCCaller

class RPCObject(object):
    _rpc_methods = {}

    @classmethod
    def register_rpc_method(cls, key, rpc_methods, *args, **kwargs):
        if cls not in cls._rpc_methods:
            cls._rpc_methods[cls] = {}

        cls._rpc_methods[cls][key] = RPCMethod(rpc_methods, *args, **kwargs)

        single_rpc_call = lambda self, *args: self.exec_rpc_call(key, *args)
        setattr(cls, key, single_rpc_call)

    @classmethod
    def get_rpc_methods(cls) -> dict:
        return dict(cls._rpc_methods[cls])

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
        rpc_method = self._rpc_methods[type(self)][key]
        return rpc_method

class BaseMulticallBuilder(object):
    __metadata_cls__ = None
    __rpc_object_cls__ = None
    __multicall_rpc_method__ = None

    def __init__(self, context: RTContext):
        self.keys = []
        self.args = []
        self.context = context
        self.available_methods = self.context.get_available_rpc_methods()

    def call(self):
        caller = RPCCaller(self.context)

        rpc_methods = list(map(lambda x: self.__rpc_object_cls__.get_rpc_methods()[x], self.keys))
        mapper = lambda x:\
            x.get_available_method_name(self.context.get_available_rpc_methods()) + '='
        self.args.extend(map(mapper, rpc_methods))
        results = caller.add(self.__multicall_rpc_method__, *self.args).call()[0]

        metadata_list = []
        for res in results:
            metadata = {}
            for i,r in enumerate(res):
                for processor in rpc_methods[i].get_post_processors():
                    r = processor(r)

                metadata[self.keys[i]] = r

            metadata_list.append(self.__metadata_cls__(metadata))

        return tuple(metadata_list)

    def __getattr__(self, item):
        self._assert_valid_rpc_method(item)
        def inner():
            self._add_rpc_method(item)
            return self

        return inner

    def _assert_valid_rpc_method(self, key):
        method = self.__rpc_object_cls__.get_rpc_methods().get(key)
        if method is None:
            raise RuntimeError("No method with key '{0}' found.".format(key))
        if not method.is_available(self.available_methods):
            raise RuntimeError("Method with key '{0}' is unavailable".format(key))
        if not method.is_retriever():
            raise RuntimeError("Modifier method with key '{0}' is not allowed".format(key))

    def _add_rpc_method(self, key):
        self.keys.append(key)
