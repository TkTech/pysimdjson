import pytest

import simdjson


def test_object_abc_mapping(parser):
    """Ensure our Object type complies with the collections.abc.Mapping
    interface.

    Complying with this interface requires `__iter__`, `__len__`,
    `__contains__`, `__getitem__`, `keys`, `items`, `values`, and `get`.
    """
    doc = parser.parse(b'{"a": "b", "c": [0, 1, 2], "x": {"f": "z"}}')
    assert isinstance(doc, simdjson.Object)

    # __iter__
    assert list(iter(doc)) == ['a', 'c', 'x']
    # __len__
    assert len(doc) == 3
    # __contains__
    assert 'a' in doc
    assert 'd' not in doc
    # __getitem__
    # Individual key access returns proxy objects.
    assert isinstance(doc['x'], simdjson.Object)
    assert isinstance(doc['c'], simdjson.Array)

    # Key lookup by byte or str
    assert doc['a'] == 'b'
    assert doc[b'a'] == 'b'

    with pytest.raises(KeyError):
        doc['z']

    # keys()
    assert list(doc.keys()) == ['a', 'c', 'x']
    # values()
    assert list(doc.values()) == ['b', [0, 1, 2], {'f': 'z'}]
    # items()
    assert list(doc.items()) == [
        ('a', 'b'),
        ('c', [0, 1, 2]),
        ('x', {'f': 'z'})
    ]
    # get()
    assert doc.get('a') == 'b'
    assert doc.get('z') is None
    assert doc.get('z', True) is True


def test_object_uplift(parser):
    """Ensure we can turn our Object into a python dict."""
    doc = parser.parse(b'{"a": "b", "c": [0, 1, 2], "x": {"f": "z"}}')
    assert isinstance(doc, simdjson.Object)

    assert doc.as_dict() == {
        'a': 'b',
        'c': [0, 1, 2],
        'x': {'f': 'z'}
    }
    assert isinstance(doc.as_dict(), dict)


def test_object_mini(parser):
    """Test JSON minifier."""
    doc = parser.parse(b'{"a" : "z" }')
    assert doc.mini == b'{"a":"z"}'


def test_object_pointer(parser):
    """Ensure we can access an object element by pointer."""
    doc = parser.parse(b'{"a" : "z" }')
    assert doc.at_pointer('/a') == 'z'
