import os, sys, re, time
sys.path.append(re.search("(.*){0}".format(__file__), os.path.abspath(__file__)).groups()[0])

import rtorrent
from pprint import pprint

if __name__ == '__main__':
	start = time.time()
	r = rtorrent.RTorrent("http://192.168.1.134:81")
	print(time.time() - start)
	r.get_torrents()

	r.torrents[0].poll()

	print(time.time() - start)
