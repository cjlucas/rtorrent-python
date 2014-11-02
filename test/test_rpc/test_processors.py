from rtorrent.rpc.processors import *

from nose.tools import *

def test_valmap1():
    mapper = valmap([0, 1, 2, 3], ['off', 'low', 'normal', 'high'])
    eq_(mapper(1), ['low'])

def test_valmap2():
    mapper = valmap([0, 1, 2, 3], ['off', 'low', 'normal', 'high'], index=1)
    arg0 = 'arg_index_0'
    eq_(mapper(arg0, 3), [arg0, 'high'])


def test_choose_int():
    chooser = choose(2)
    eq_(chooser(0, 2, 4, 6), 4)

def test_choose_iter():
    chooser = choose([0, 2, 4])
    results = chooser('one', 'two', 'three', 'four', 'five')
    eq_(len(results), 3)
    eq_(results[0], 'one')
    eq_(results[1], 'three')
    eq_(results[2], 'five')

def test_int_to_bool():
    eq_(int_to_bool(1),     True)
    eq_(int_to_bool('1'),   True)
    eq_(int_to_bool(0),     False)
    eq_(int_to_bool('0'),   False)

def test_bool_to_int():
    eq_(bool_to_int(True), 1)
    eq_(bool_to_int(False), 0)

def test_check_success():
    eq_(check_success(0), True)
    eq_(check_success(-1), False)

def test_to_datetime():
    input = 1414776586757462
    expected = datetime.datetime(2014, 10, 31, 10, 29, 46, 757462)
    delta = to_datetime(input) - expected
    print(delta)
    assert abs(delta) < datetime.timedelta(microseconds=10)
