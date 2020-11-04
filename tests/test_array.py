"""Tests for the csimdjson.Array proxy object."""
import collections.abc

import pytest

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
    # count()
    assert obj.count(3) == 1
    # index(x)
    assert obj.index(5) == 4
    # index(x, start)
    with pytest.raises(ValueError):
        assert obj.index(1, 2)
    assert obj.index(4, 2) == 3
    # index(x, start, end)
    with pytest.raises(ValueError):
        assert obj.index(4, 1, -5)
    assert obj.index(4, 0, -1) == 3


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
    assert doc.mini == '[0,1,2,3,4,5]'


def test_array_as_buffer(parser):
    """Ensure we can export homogeneous arrays as buffers."""
    doc = parser.parse(b'''{
        "d": [1.2, 2.3, 3.4],
        "i": [-1, 2, -3, 4],
        "u": [1, 2, 3, 4, 5],
        "x": [1, 2, 3, "not valid"]
    }''')

    view = memoryview(doc['d'].as_buffer(of_type='d'))
    assert view.readonly is False
    assert len(view) == 3
    assert view.itemsize == 8

    view = memoryview(doc['i'].as_buffer(of_type='i'))
    assert view.readonly is False
    assert len(view) == 4
    assert view.itemsize == 8

    view = memoryview(doc['u'].as_buffer(of_type='u'))
    assert view.readonly is False
    assert len(view) == 5
    assert view.itemsize == 8

    # Not a valid `of_type`.
    with pytest.raises(ValueError):
        doc['i'].as_buffer(of_type='x')

    # Not a valid homogeneous array.
    with pytest.raises(TypeError):
        doc['x'].as_buffer(of_type='u')

    # Signed elements should error on cast.
    with pytest.raises(ValueError):
        doc['i'].as_buffer(of_type='u')

    # Ensure n-dimensional arrays are flattened.
    doc = parser.parse(b'''[[
        [1.0, 2.0],
        [3.0, 4.0]
    ]]''')
    view = memoryview(doc.as_buffer(of_type='d'))
    assert view.readonly is False
    assert len(view) == 4
    assert view.itemsize == 8


def test_array_slots(parser):
    """Esure we're getting the correct number of tape slots."""
    doc = parser.parse(b'[0, 1, 2, 3, 4, 5]')
    assert doc.slots == 14
