import os, sys, re, time
sys.path.append(re.search("(.*){0}".format(__file__), os.path.abspath(__file__)).groups()[0])

import rtorrent

def main():
	torrent_file, torrent_path = sys.argv[1:3]

	if "/Volumes/" in torrent_path: torrent_path = torrent_path.replace("Volumes", "mnt/user")
	r = rtorrent.RTorrent("http://192.168.1.134:81")
	r._p.set_xmlrpc_size_limit(4194304)
	t = r.load_torrent(os.path.abspath(torrent_file))
	t.set_directory(torrent_path)
	t.start()


if __name__ == '__main__':
	main()
