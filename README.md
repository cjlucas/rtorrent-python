ABOUT THIS PROJECT
------------------
The xmlrpc interface to rTorrent is extremely unintuitive and has very little documentation, this library aims to make interfacing with rTorrent much easier.

REQUIREMENTS
------------
- [rTorrent] (http://libtorrent.rakshasa.no/) 0.7.5 or later, with xmlrpc-c support using [this guide] (http://libtorrent.rakshasa.no/wiki/RTorrentXMLRPCGuide).
- [xmlrpc-c] (http://xmlrpc-c.sourceforge.net/) 1.00 or later. 1.07 or later for 64bit integer support (highly recommended, download either the stable or advanced branches).
- [Apache] (http://www.apache.org/) or [lighttpd] (http://www.lighttpd.net/)


TODO
----
- Add update() functions for each of the classes (Torrent, Peer, File, Tracker)
- Add support for get/set functions for Peer
- Documentation and examples
