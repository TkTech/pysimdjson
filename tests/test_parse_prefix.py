import pytest

from pysimdjson import parse_prefix

def test_parse_prefix():
    # Simple unquoted string with a delimiter.
    assert parse_prefix('test.string') == [b'test', b'string']
    # Quoted string with an escaped quote within it.
    assert parse_prefix('"t\\"t"') == [b't"t']
    # Quoted string followed by delimiter and unquoted string.
    assert parse_prefix('"test".string') == [b'test', b'string']

    with pytest.raises(ValueError):
        parse_prefix('"')

    with pytest.raises(ValueError):
        parse_prefix('"\\')
