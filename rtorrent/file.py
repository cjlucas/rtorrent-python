from rtorrent.rpc.object import RPCObject

class File(RPCObject):
    def __init__(self, context, info_hash, index):
        super().__init__(context)
        self.rpc_id = "{0}:f{1}".format(info_hash, index)

    def rpc_call(self, key, *args):
        call = super().rpc_call(key, *args)
        call.get_args().insert(0, self.rpc_id)
        return call


File.register_rpc_method('get_size', 'f.get_size_bytes')
