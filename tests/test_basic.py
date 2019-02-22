import json

import pytest

import pysimdjson

def test_valid_smallblock():
    assert pysimdjson.loads(b'{"test": "value"}') == {
        'test': 'value'
    }


def test_invalid_smallblock():

    with pytest.raises(json.JSONDecodeError):
        pysimdjson.loads(b'{"test":}')
