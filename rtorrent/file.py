from rtorrent.rpc import RPCObject, BaseMulticallBuilder

from rtorrent.rpc.processors import *

class File(RPCObject):
    def __init__(self, context, info_hash, index):
        super().__init__(context)
        self.rpc_id = "{0}:f{1}".format(info_hash, index)

    def rpc_call(self, key, *args):
        call = super().rpc_call(key, *args)
        call.get_args().insert(0, self.rpc_id)
        return call


class FileMulticallBuilder(BaseMulticallBuilder):
    def __init__(self, context, torrent):
        super().__init__(context)
        self.args.extend([torrent.get_info_hash(), ''])
        self.multicall_rpc_method = 'f.multicall'
        self.rpc_object_class = File
        self.metadata_cls = FileMetadata

class FileMetadata(object):
    def __init__(self, results: dict):
        self.results = results

    def __getattr__(self, item):
        return lambda: self.results[item]

_VALID_FILE_PRIORITiES = ['off', 'normal', 'high']

File.register_rpc_method('get_size', 'f.get_size_bytes')
File.register_rpc_method('get_path', 'f.get_path')
File.register_rpc_method('get_priority', 'f.get_priority',
                         post_processors=[lambda x:
                                          _VALID_FILE_PRIORITiES[x]])
File.register_rpc_method('set_priority', 'f.set_priority',
                         pre_processors=[valmap(_VALID_FILE_PRIORITiES,
                                                range(0, 3), 1)],
                         post_processors=[check_success])