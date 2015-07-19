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


class FileMetadata(object):
    def __init__(self, results: dict):
        self.results = results

    def __getattr__(self, item):
        return lambda: self.results[item]

class FileMulticallBuilder(BaseMulticallBuilder):
    __metadata_cls__ = FileMetadata
    __rpc_object_cls__ = File
    __multicall_rpc_method__ = 'f.multicall'

    def __init__(self, context, torrent):
        super().__init__(context)
        self.args.extend([torrent.get_info_hash(), ''])

_VALID_FILE_PRIORITiES = ['off', 'normal', 'high']

File.register_rpc_method('get_size_bytes', 'f.get_size_bytes')
File.register_rpc_method('get_size_chunks', 'f.get_size_chunks')
File.register_rpc_method('get_path', 'f.get_path')
File.register_rpc_method('get_priority', 'f.get_priority',
                         post_processors=[lambda x:
                                          _VALID_FILE_PRIORITiES[x]])
File.register_rpc_method('set_priority', 'f.set_priority',
                         pre_processors=[valmap(_VALID_FILE_PRIORITiES,
                                                range(0, 3), 1)],
                         post_processors=[check_success])
File.register_rpc_method('get_completed_chunks', 'f.completed_chunks')
File.register_rpc_method('get_frozen_path', 'f.frozen_path')
File.register_rpc_method('get_last_touched', 'f.get_last_touched',
                         post_processors=[to_datetime])
File.register_rpc_method('get_offset', 'f.get_offset')
File.register_rpc_method('get_path_components', 'f.get_path_components')
File.register_rpc_method('get_path_depth', 'f.get_path_depth')
File.register_rpc_method('get_range_first', 'f.get_range_first')
File.register_rpc_method('get_range_second', 'f.get_range_second')
File.register_rpc_method('is_created_queued', 'f.is_created_queued',
                         bool=True)
