from rtorrent.rpc import RPCObject, BaseMulticallBuilder

from rtorrent.rpc.processors import *


class Tracker(RPCObject):
    def __init__(self, context, info_hash, index):
        super().__init__(context)
        self.rpc_id = "{0}:t{1}".format(info_hash,index)
    
    def rpc_call(self, key, *args):
        call = super().rpc_call(key, *args)
        call.get_args().insert(0, self.rpc_id)
        return call

class TrackerMetadata(object):
    def __init__(self, results):
        self.results = results

    def __getattr__(self, item):
        return lambda: self.results[item]


class TrackerMulticallBuilder(BaseMulticallBuilder):
    __metadata_cls__ = TrackerMetadata
    __rpc_object_cls__ = Tracker
    __multicall_rpc_method__ = 't.multicall'
    
    def __init__(self, context, torrent):
        super().__init__(context)
        self.args.extend([torrent.get_info_hash(), ''])


Tracker.register_rpc_method('is_enabled', 't.is_enabled', boolean=True)
Tracker.register_rpc_method('get_id', 't.get_id')
Tracker.register_rpc_method('get_scrape_incomplete', 't.get_scrape_incomplete')
Tracker.register_rpc_method('is_open', 't.is_open', boolean=True)
Tracker.register_rpc_method('get_min_interval', 't.get_min_interval')
Tracker.register_rpc_method('get_scrape_downloaded', 't.get_scrape_downloaded')
Tracker.register_rpc_method('get_group', 't.get_group')
Tracker.register_rpc_method('get_scrape_time_last', 't.get_scrape_time_last',
        post_processors=[s_to_datetime])
Tracker.register_rpc_method('get_type', 't.get_type')
Tracker.register_rpc_method('get_normal_interval', 't.get_normal_interval')
Tracker.register_rpc_method('get_url', 't.get_url')
Tracker.register_rpc_method('get_scrape_complete', 't.get_scrape_complete')
Tracker.register_rpc_method('get_activity_time_last', 't.activity_time_last',
        post_processors=[s_to_datetime])
Tracker.register_rpc_method('get_activity_time_next', 't.activity_time_next',
        post_processors=[s_to_datetime])
Tracker.register_rpc_method('get_failed_time_last', 't.failed_time_last',
        post_processors=[s_to_datetime])
Tracker.register_rpc_method('get_failed_time_next', 't.failed_time_next',
        post_processors=[s_to_datetime])
Tracker.register_rpc_method('get_success_time_last', 't.success_time_last',
        post_processors=[s_to_datetime])
Tracker.register_rpc_method('get_success_time_next', 't.success_time_next',
        post_processors=[s_to_datetime])
Tracker.register_rpc_method('can_scrape', 't.can_scrape', boolean=True)
Tracker.register_rpc_method('get_failed_counter', 't.failed_counter')
Tracker.register_rpc_method('get_scrape_counter', 't.scrape_counter')
Tracker.register_rpc_method('get_success_counter', 't.success_counter')
Tracker.register_rpc_method('is_usable', 't.is_usable', boolean=True)
Tracker.register_rpc_method('is_busy', 't.is_busy', boolean=True)
Tracker.register_rpc_method('is_extra_tracker', 't.is_extra_tracker', boolean=True)
Tracker.register_rpc_method("get_latest_sum_peers", "t.latest_sum_peers")
Tracker.register_rpc_method("get_latest_new_peers", "t.latest_new_peers")

