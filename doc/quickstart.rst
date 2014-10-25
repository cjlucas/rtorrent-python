Getting Started
===============

Installing RTorrent
-------------------

RTorrent is available for both Linux and OS X. Below are instructions for your specific system.

.. TODO: document installing from source

Mac OS X
^^^^^^^^

RTorrent can be easily installed using `Homebrew <http://brew.sh/>`_.

.. code-block:: bash

    $ brew install rtorrent --with-xmlrpc-c

Ubuntu
^^^^^^

The RTorrent has XML-RPC support already builtin.

.. code-block:: bash

    $ sudo apt-get install rtorrent

Gentoo
^^^^^^

To install RTorrent with XML-RPC support, ensure the proper USE flag is added.

.. code-block:: bash

    $ sudo echo "net-p2p/rtorrent xmlrpc" >> /etc/portage/package.use
    $ sudo emerge rtorrent

Configuring RTorrent
--------------------

In order to open RTorrent's XMLRPC interface, ``scgi_port`` must be set in your `~/.rtorrent.rc`::

    scgi_port = localhost:5000

.. TODO: document scgi_local

Configuring HTTP Access
-----------------------

.. TODO: document scgi setup

Nginx:

.. code-block:: nginx

    server {
        listen 0.0.0.0:80
        location /RPC2 {
            include scgi_params;
            scgi_pass localhost:5000
        }
    }


Installing rtorrent-python
--------------------------

rtorrent-python is easily installed by using the `pip <https://pypi.python.org/pypi/pip>`_ tool:

.. code-block:: bash

    $ pip install rtorrent

.. TODO: docuement manually installation
