import xmlrpc.client

from rtorrent.rpc import RPCObject
from rtorrent.context import RTContext
from rtorrent.rpc.caller import RPCCaller

from rtorrent.torrent import Torrent, TorrentMulticallBuilder

class RTorrent(RPCObject, RTContext):
    def __init__(self, url):
        super().__init__(self)
        self.url = url
        self.available_rpc_methods = None

    def get_conn(self):
        return xmlrpc.client.ServerProxy(self.url, verbose=False)

    def get_available_rpc_methods(self):
        if self.available_rpc_methods is None:
            self.available_rpc_methods = self.get_conn().system.listMethods()

        return self.available_rpc_methods

    def get_torrents(self, view=None) -> [Torrent]:
        metadata_list =  TorrentMulticallBuilder(self, view).get_info_hash().call()
        return [Torrent(self, x.get_info_hash()) for x in metadata_list]
