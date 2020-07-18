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

    assert isinstance(doc, csimdjson.Array)
    assert list(doc) == [0, 1, 2, 3, 4, 5]
    assert doc[-1] == 5
    assert doc[0:2] == [0, 1]
    assert doc[::2] == [0, 2, 4]
    assert doc[::-1] == [5, 4, 3, 2, 1, 0]

    # Converting to a list recursively uplifts.
    assert doc.as_list() == [0, 1, 2, 3, 4, 5]


def test_object(parser):
    """Ensure we can access a csimdjson.Object just a like a Mapping."""
    doc = parser.parse(b'{"a": "b", "c": [0, 1, 2], "x": {"f": "z"}}')

    # We implement __contains__, no uplifting required.
    assert 'a' in doc
    assert 'd' not in doc

    # Both keys() and values() recursively uplift Array and Object, or 99%
    # of things expecting a Mapping would break.
    assert doc.keys() == ['a', 'c', 'x']
    assert doc.values() == ['b', [0, 1, 2], {'f': 'z'}]

    # But individual key access returns proxy objects.
    assert isinstance(doc["x"], csimdjson.Object)
    assert isinstance(doc["c"], csimdjson.Array)

    # Converting to a dict recursively uplifts.
    assert doc.as_dict() == {
        'a': 'b',
        'c': [0, 1, 2],
        'x': {'f': 'z'}
    }
