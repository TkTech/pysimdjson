import json

import pytest

import simdjson


def test_valid_smallblock():
    assert simdjson.loads(b'{"test": "value"}') == {
        'test': 'value'
    }


def test_invalid_smallblock():
    with pytest.raises(json.JSONDecodeError):
        simdjson.loads(b'{"test":}')
