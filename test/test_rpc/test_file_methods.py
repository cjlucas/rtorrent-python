import datetime
import unittest

from nose.tools import *

from rtorrent.file import File

INFO_HASH = '1D226C20D67F8F2DDEE4FD99A880974B3F2B6F1E'

f = File(None, INFO_HASH, 0)

class TestSetPriority(unittest.TestCase):
    def test_pre_processing1(self):
        call = self._get_call('off')
        call.do_pre_processing()
        eq_(call.get_args(), [f.rpc_id, 0])

    def test_pre_processing3(self):
        call = self._get_call('normal')
        call.do_pre_processing()
        eq_(call.get_args(), [f.rpc_id, 1])

    def test_pre_processing4(self):
        call = self._get_call('high')
        call.do_pre_processing()
        eq_(call.get_args(), [f.rpc_id, 2])

    def test_post_processing(self):
        call = self._get_call()
        result = call.do_post_processing(0)
        eq_(result, True)

    def _get_call(self, *args):
        return f.rpc_call('set_priority', *args)

class TestGetPriority(unittest.TestCase):
    def setUp(self):
        self.call = f.rpc_call('get_priority')


    def test_post_processing1(self):
        result = self.call.do_post_processing(0)
        eq_(result, 'off')

    def test_post_processing3(self):
        result = self.call.do_post_processing(1)
        eq_(result, 'normal')

    def test_post_processing4(self):
        result = self.call.do_post_processing(2)
        eq_(result, 'high')

class TestGetLastTouched(unittest.TestCase):
    def setUp(self):
        self.call = f.rpc_call('get_last_touched')

    def test_pre_processing(self):
        self.call.do_pre_processing()
        eq_(self.call.get_args(), [f.rpc_id])

    def test_post_processing(self):
        result = self.call.do_post_processing(1414776586757462)
        eq_(result, datetime.datetime(2014, 10, 31, 10, 29, 46, 757462))
