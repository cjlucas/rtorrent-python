from rtorrent.rpc import RPCObject
from rtorrent.rpc.method import check_success
from rtorrent.rpc.caller import RPCCaller
from rtorrent.rpc import BaseMulticallBuilder
import rtorrent.file

from rtorrent.rpc.processors import *

class Torrent(RPCObject):
    def __init__(self, context, info_hash):
        super().__init__(context)
        self.info_hash = info_hash

    def rpc_call(self, key, *args):
        call = super().rpc_call(key, *args)
        # inject required info_hash argument as first argument
        call.get_args().insert(0, self.info_hash)
        return call

    def get_file_metadata(self):
        return rtorrent.file.FileMulticallBuilder(self.context, self) \
            .get_size() \
            .get_priority() \
            .get_path() \
            .call()

    def __str__(self):
        return "Torrent(info_hash={0})".format(self.info_hash)


class TorrentMulticallBuilder(BaseMulticallBuilder):
    def __init__(self, context, view):
        super().__init__(context)
        if view is None:
            view = 'main'
        self.keys.insert(0, 'get_info_hash')
        self.args.insert(0, [view])
        self.multicall_rpc_method = 'd.multicall'
        self.rpc_object_class = Torrent
        self.metadata_cls = TorrentMetadata


class TorrentMetadata(object):
    def __init__(self, results: dict):
        self.results = results

    def __getattr__(self, item):
        return lambda: self.results[item]


_VALID_TORRENT_PRIORITIES = ['off', 'low', 'normal', 'high']

Torrent.register_rpc_method('get_info_hash', 'd.get_hash')
Torrent.register_rpc_method("set_priority", "d.set_priority",
                            pre_processors=[valmap(_VALID_TORRENT_PRIORITIES,
                                                   range(0, 4), 1)],
                            post_processors=[check_success])
Torrent.register_rpc_method("get_priority", "d.get_priority",
                            post_processors=[lambda x:
                                             _VALID_TORRENT_PRIORITIES[x]])
Torrent.register_rpc_method("is_accepting_seeders", "d.accepting_seeders",
                            boolean=True)
