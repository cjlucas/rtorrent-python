import unittest
from nose.tools import *

from rtorrent.torrent import Torrent

INFO_HASH = '1D226C20D67F8F2DDEE4FD99A880974B3F2B6F1E'

t = Torrent(None, INFO_HASH)

class TestGetInfoHash(unittest.TestCase):
    def setUp(self):
        self.call = t.rpc_call('get_info_hash')

    def test_pre_processing(self):
        self.call.do_pre_processing()
        eq_(self.call.get_args(), [INFO_HASH])

    def test_post_processing(self):
        result = self.call.do_post_processing(INFO_HASH)
        eq_(result, INFO_HASH)

class TestSetPriority(unittest.TestCase):
    def test_pre_processing1(self):
        call = self._get_call('off')
        call.do_pre_processing()
        eq_(call.get_args(), [INFO_HASH, 0])

    def test_pre_processing2(self):
        call = self._get_call('low')
        call.do_pre_processing()
        eq_(call.get_args(), [INFO_HASH, 1])

    def test_pre_processing3(self):
        call = self._get_call('normal')
        call.do_pre_processing()
        eq_(call.get_args(), [INFO_HASH, 2])

    def test_pre_processing4(self):
        call = self._get_call('high')
        call.do_pre_processing()
        eq_(call.get_args(), [INFO_HASH, 3])

    def test_post_processing(self):
        call = self._get_call()
        result = call.do_post_processing(0)
        eq_(result, True)

    def _get_call(self, *args):
        return t.rpc_call('set_priority', *args)

class TestGetPriority(unittest.TestCase):
    def setUp(self):
        self.call = t.rpc_call('get_priority')

    def test_pre_processing(self):
        self.call.do_pre_processing()
        eq_(self.call.get_args(), [INFO_HASH])

    def test_post_processing1(self):
        result = self.call.do_post_processing(0)
        eq_(result, 'off')

    def test_post_processing2(self):
        result = self.call.do_post_processing(1)
        eq_(result, 'low')

    def test_post_processing3(self):
        result = self.call.do_post_processing(2)
        eq_(result, 'normal')

    def test_post_processing4(self):
        result = self.call.do_post_processing(3)
        eq_(result, 'high')


class TestIsAcceptingSeeders(unittest.TestCase):
    def setUp(self):
        self.call = t.rpc_call('is_accepting_seeders')

    def test_pre_processing(self):
        self.call.do_pre_processing()
        eq_(self.call.get_args(), [INFO_HASH])

    def test_post_processing1(self):
        result = self.call.do_post_processing(0)
        eq_(result, False)


    def test_post_processing2(self):
        result = self.call.do_post_processing(1)
        eq_(result, True)

