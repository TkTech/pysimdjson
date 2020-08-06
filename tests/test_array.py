"""Tests for the csimdjson.Array proxy object."""
import pytest

import simdjson


def test_abc_sequence(parser):
    """Ensure our Array type complies with the collections.abc.Sequence
    interface.

    Complying with this interface requires `__iter__`, `__len__`,
    `__contains__`, `__getitem__`, `__reversed__`, `index`, and `count`.
    """
    obj = parser.parse(b'[1, 2, 3, 4, 5]')
    assert isinstance(obj, simdjson.Array)

    # __iter__
    for left, right in zip(obj, [1, 2, 3, 4, 5]):
        assert left == right
    # __len__
    assert len(obj) == 5
    # __getitem__
    assert obj[2] == 3
    # __contains__
    assert 3 in obj
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
