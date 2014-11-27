import sys

from rtorrent.torrent import Torrent
from rtorrent.file import File
from rtorrent import RTorrent

def main():
    rt = RTorrent(sys.argv[-1])
    all_methods = rt.get_available_rpc_methods()


    supported_methods = []
    for cls in [Torrent, File]:
        for key, rpc_method in cls.get_rpc_methods().items():
            supported_methods.extend(rpc_method.get_method_names())


    for method in supported_methods:
        i = all_methods.index(method)
        del all_methods[i]

    for m in all_methods:
        print(m)

if __name__ == '__main__':
    main()