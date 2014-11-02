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

_VALID_FILE_PRIORITIES = ['off', 'normal', 'high']

File.register_rpc_method('get_size_bytes',
                         ['f.get_size_bytes', 'f.size_bytes'])
File.register_rpc_method('get_size_chunks',
                         ['f.get_size_chunks', 'f.size_chunks'])
File.register_rpc_method('get_path', ['f.get_path', 'f.path'])
File.register_rpc_method('get_priority', ['f.get_priority', 'f.priority'],
                         post_processors=[lambda x:
                                          _VALID_FILE_PRIORITIES[x]])
File.register_rpc_method('set_priority', ['f.set_priority', 'f.priority.set'],
                         pre_processors=[valmap(_VALID_FILE_PRIORITIES,
                                                range(0, 3), 1)],
                         post_processors=[check_success])
File.register_rpc_method('get_completed_chunks', 'f.completed_chunks')
File.register_rpc_method('get_frozen_path', 'f.frozen_path')
File.register_rpc_method('get_last_touched',
                         ['f.get_last_touched', 'f.last_touched'],
                         post_processors=[to_datetime])
File.register_rpc_method('get_offset', ['f.get_offset', 'f.offset'])
File.register_rpc_method('get_path_components',
                         ['f.get_path_components', 'f.path_components'])
File.register_rpc_method('get_path_depth',
                         ['f.get_path_depth', 'f.path_depth'])
File.register_rpc_method('get_range_first',
                         ['f.get_range_first', 'f.range_first'])
File.register_rpc_method('get_range_second',
                         ['f.get_range_second', 'f.range_second'])
File.register_rpc_method('is_create_queued', 'f.is_create_queued',
                         boolean=True)
File.register_rpc_method('is_open', 'f.is_open',
                         boolean=True)
File.register_rpc_method('get_completed_chunks',
                         ['f.get_completed_chunks', 'f.completed_chunks'])
File.register_rpc_method('get_match_depth_next',
                         ['f.get_match_depth_next', 'f.match_depth_next'])
File.register_rpc_method('get_match_depth_prev',
                         ['f.get_match_depth_prev', 'f.match_depth_prev'])
File.register_rpc_method('is_prioritized_first', 'f.prioritize_first',
                         boolean=True)
File.register_rpc_method('enable_prioritize_first',
                         'f.prioritize_first.enable',
                         post_processor=[check_success])
File.register_rpc_method('disable_prioritize_first',
                         'f.prioritize_first.disable',
                         post_processor=[check_success])
File.register_rpc_method('is_prioritized_last', 'f.prioritize_last',
                         boolean=True)
File.register_rpc_method('enable_prioritize_last',
                         'f.prioritize_last.enable',
                         post_processor=[check_success])
File.register_rpc_method('disable_prioritize_last',
                         'f.prioritize_last.disable',
                         post_processor=[check_success])
File.register_rpc_method('is_created', 'f.is_created',
                         boolean=True)