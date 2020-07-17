import pytest

import csimdjson


def test_json_pointer(parser):
    """Ensure JSON pointers work as expected and all possible exceptions
    are converted to Python types.
    """
    doc = parser.parse(b'{"key": "value", "array": [0, 1, 2]}')

    assert isinstance(doc.at('key'), str)
    assert isinstance(doc.at('array/0'), int)
    assert isinstance(doc / 'array' / '0', int)

    with pytest.raises(csimdjson.NoSuchFieldError):
        doc.at('no_such_key')

    with pytest.raises(csimdjson.IndexOutOfBoundsError):
        doc.at('array/9')

    with pytest.raises(csimdjson.IncorrectTypeError):
        doc.at('array/not_a_num')

    with pytest.raises(csimdjson.InvalidJSONPointerError):
        doc.at('array/')


def test_getitem(parser):
    """Ensure accessing a specific element works as expected."""
    doc = parser.parse(b'''{"key": "value"}''')

    with pytest.raises(KeyError):
        doc['no_such_key']

    assert doc['key'] == 'value'

    doc = parser.parse(b'''[0, 1, 2]''')

    assert doc[1] == 1

def test_uplift(doc):
    """Ensure every JSON type is uplifted to the proper Python type."""
    assert isinstance(doc['array'], csimdjson.Array)
    assert isinstance(doc['object'], csimdjson.Object)
    assert doc['int64'] == -1
    assert doc['uint64'] == 18446744073709551615
    assert doc['double'] == 1.1
    assert doc['string'] == 'test'
    assert doc['bool'] is True
    assert doc['null_value'] is None

def test_array_slicing(parser):
    """Ensure we can slice our csimdjson.Array just like a real array."""
    doc = parser.parse(b'[0, 1, 2, 3, 4, 5]')

    assert list(doc) == [0, 1, 2, 3, 4, 5]
    assert doc[-1] == 5
    assert doc[0:2] == [0, 1]
    assert doc[::2] == [0, 2, 4]
    assert doc[::-1] == [5, 4, 3, 2, 1, 0]

def test_object(parser):
    doc = parser.parse(b'{"a": "b", "c": [0, 1, 2]}')

    assert 'a' in doc
    assert 'd' not in doc

    assert doc.keys() == ['a', 'c']
    assert doc.values() == ['b', [0, 1, 2]]
