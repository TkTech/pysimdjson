"""Tests for the csimdjson.Array proxy object."""
import pytest
import json

import simdjson


def test_array_abc_sequence(parser):
    """Ensure our Array type complies with the collections.abc.Sequence
    interface.

    Complying with this interface requires `__iter__`, `__len__`,
    `__contains__`, `__getitem__`, `__reversed__`, `index`, and `count`.
    """
    obj = parser.parse(b'[1, 2, 3, 4, 5]')
    assert isinstance(obj, simdjson.Array)

    # __iter__
    assert list(iter(obj)) == [1, 2, 3, 4, 5]
    # __len__
    assert len(obj) == 5
    # __contains__
    assert 3 in obj
    assert 7 not in obj
    # __getitem__
    assert obj[2] == 3
    with pytest.raises(IndexError):
        obj[99]
    # __reversed__, implemented via __len__ and __getitem__ for now.
    assert list(reversed(obj)) == [5, 4, 3, 2, 1]


def test_array_slicing(parser):
    """Ensure we can slice our csimdjson.Array just like a real array."""
    doc = parser.parse(b'[0, 1, 2, 3, 4, 5]')
    assert isinstance(doc, simdjson.Array)

    assert list(doc) == [0, 1, 2, 3, 4, 5]
    assert doc[-1] == 5
    assert doc[0:2] == [0, 1]
    assert doc[::2] == [0, 2, 4]
    assert doc[::-1] == [5, 4, 3, 2, 1, 0]


def test_array_uplift(parser):
    """Ensure we can turn our Array into a python list."""
    doc = parser.parse(b'[0, 1, 2, 3, 4, 5]')
    assert isinstance(doc, simdjson.Array)

    assert doc.as_list() == [0, 1, 2, 3, 4, 5]
    assert isinstance(doc.as_list(), list)


def test_array_mini(parser):
    """Test JSON minifier."""
    doc = parser.parse(b'[ 0, 1, 2,    3, 4, 5]')
    assert doc.mini == b'[0,1,2,3,4,5]'


def test_array_as_buffer(parser):
    """Ensure we can export homogeneous arrays as buffers."""
    doc = parser.parse(b'''{
        "d": [1.2, 2.3, 3.4],
        "i": [-1, 2, -3, 4],
        "u": [1, 2, 3, 4, 5],
        "x": [1, 2, 3, "not valid"]
    }''')

    memoryview(doc['d'].as_buffer(of_type='d'))
    memoryview(doc['i'].as_buffer(of_type='i'))
    memoryview(doc['u'].as_buffer(of_type='u'))

    # Not a valid `of_type`.
    with pytest.raises(ValueError):
        doc['i'].as_buffer(of_type='x')

    # Not a valid homogeneous array.
    with pytest.raises(TypeError):
        doc['x'].as_buffer(of_type='u')

    # Signed elements should error on cast.
    with pytest.raises(ValueError):
        doc['i'].as_buffer(of_type='u')


def test_array_as_buffer_ndim(parser):
    """Ensure n-dimensional arrays are flattened when converting to a
    buffer."""
    doc = parser.parse(b'''[[
        [1.0, 2.0],
        [3.0, 4.0]
    ]]''')
    view = memoryview(doc.as_buffer(of_type='d'))
    assert len(view) == 32


def test_array_pointer(parser):
    """Ensure we can access an array element by pointer."""
    doc = parser.parse(b'[0, 1, 2, 3, 4, 5]')
    assert doc.at_pointer('/1') == 1


@pytest.mark.parametrize('key', [0.0, 1.5, '0', None, object()])
def test_array_invalid_index(parser, key):
    doc = parser.parse(b'[10, 20]')
    with pytest.raises(TypeError):
        doc[key]


@pytest.mark.parametrize('key', [2, -3, 2**40, -(2**40), 2**100, -(2**100)])
def test_array_index_bounds(parser, key):
    doc = parser.parse(b'[10, 20]')
    with pytest.raises(IndexError):
        doc[key]


def test_array_index_protocol(parser):
    class Index:
        def __index__(self):
            return -1

    doc = parser.parse(b'[10, 20]')
    assert doc[Index()] == 20
    assert doc[False] == 10
    assert doc[True] == 20


@pytest.mark.parametrize('values', [[], [0], [0, {'x': [1, 2]}, [3], 4, 5, 6]])
def test_array_slice_matches_list(parser, values):
    doc = parser.parse(json.dumps(values))
    bounds = [None, -100, -7, -2, -1, 0, 1, 3, 6, 100, 2**100, -(2**100)]
    for start in bounds:
        for stop in bounds:
            for step in [None, 1, 2, 3, -1, -2, -3, 2**100, -(2**100)]:
                key = slice(start, stop, step)
                assert doc[key] == values[key], key
    with pytest.raises(ValueError):
        doc[::0]


def test_array_large_tail_slice(parser):
    values = list(range(200000))
    doc = parser.parse(json.dumps(values))
    assert doc[-2000:] == values[-2000:]
    assert doc[-1:-2001:-3] == values[-1:-2001:-3]


@pytest.mark.parametrize('encode', [str, str.encode])
def test_array_pointer_nul(parser, encode):
    doc = parser.parse(b'[{"a":1,"a\\u0000b":2}]')
    assert doc.at_pointer(encode('/0/a\0b')) == 2
    with pytest.raises(KeyError):
        doc.at_pointer(encode('/0/a\0z'))
    with pytest.raises(TypeError):
        doc.at_pointer(encode('/0\0'))
