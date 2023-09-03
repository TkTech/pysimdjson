import pytest


def test_json_pointer(parser):
    """Ensure JSON pointers work as expected and all possible exceptions
    are converted to Python types.
    """
    doc = parser.parse(b'{"key": "value", "array": [0, 1, 2]}')

    assert isinstance(doc.at_pointer('/key'), str)
    assert isinstance(doc.at_pointer('/array/0'), int)

    with pytest.raises(KeyError):
        doc.at_pointer('/no_such_key')

    with pytest.raises(IndexError):
        doc.at_pointer('/array/9')

    with pytest.raises(TypeError):
        doc.at_pointer('/array/not_a_num')

    with pytest.raises(ValueError):
        doc.at_pointer('/array/')


def test_uplift(doc):
    """Test uplifting of primitive types to their Python types."""
    obj = doc.as_object
    assert obj['int64'] == -1
    assert obj['uint64'] == 18446744073709551615
    assert obj['double'] == 1.1
    assert obj['string'] == 'test'
    assert obj['bool'] is True
    assert obj['null_value'] is None
