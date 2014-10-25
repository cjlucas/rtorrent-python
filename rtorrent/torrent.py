from rtorrent.rpc.object import RPCObject
from rtorrent.rpc.method import check_success
from rtorrent.rpc.caller import RPCCaller

class Torrent(RPCObject):
    def __init__(self, context, info_hash):
        super().__init__(context)
        self.info_hash = info_hash

    def rpc_call(self, key, *args):
        call = super().rpc_call(key, *args)
        # inject required info_hash argument as first argument
        call.get_args().insert(0, self.info_hash)
        return call

    def __str__(self):
        return "Torrent(info_hash={0})".format(self.info_hash)


class TorrentMulticallBuilder(object):
    def __init__(self, context):
        self.keys = ['get_info_hash']
        self.context = context
        self.available_methods = self.context.get_available_rpc_methods()

    def call(self):
        caller = RPCCaller(self.context)

        rpc_methods = list(map(lambda x: Torrent.get_rpc_methods()[x], self.keys))
        mapper = lambda x:\
            x.get_available_method_name(self.available_methods) + '='
        args = list(map(mapper, rpc_methods))
        args.insert(0, 'main')
        results = caller.add('d.multicall', *args).call()[0]

        torrents = []
        for res in results:
            metadata = {}
            for i,r in enumerate(res):
                for processor in rpc_methods[i].get_post_processors():
                    r = processor(r)

                metadata[self.keys[i]] = r

            torrents.append(TorrentMetadata(metadata))

        return torrents

    def __getattr__(self, item):
        self._assert_valid_rpc_method(item)
        def inner():
            self._add_rpc_method(item)
            return self

        return inner

    def _assert_valid_rpc_method(self, key):
        method = Torrent.get_rpc_methods().get(key)
        if method is None:
            raise RuntimeError("No method with key '{0}' found.".format(key))
        if not method.is_available(self.available_methods):
            raise RuntimeError("Method with key '{0}' is unavailable".format(key))
        if not method.is_retriever():
            raise RuntimeError("Modifier method with key '{0}' is not allowed".format(key))

    def _add_rpc_method(self, key):
        self.keys.append(key)


class TorrentMetadata(object):
    def __init__(self, results: dict):
        self.results = results

    def __getattr__(self, item):
        return lambda: self.results[item]


Torrent.register_rpc_method('get_info_hash', 'd.get_hash')
Torrent.register_rpc_method("set_priority", "d.set_priority",
                            pre_processors=[lambda info_hash, x: [info_hash, \
                                ["off", "low", "normal", "high"].index(x)]],
                            post_processors=[check_success])

Torrent.register_rpc_method("get_priority", "d.get_priority",
                            post_processors=[lambda x: ["off", "low", "normal", "high"][x]])

Torrent.register_rpc_method("is_accepting_seeders", "d.accepting_seeders", boolean=True)
