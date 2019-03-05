from json import JSONDecodeError

import pytest

from simdjson import ParsedJson


def test_allocation_error():
    pj = ParsedJson()
    with pytest.raises(JSONDecodeError) as exc:
        pj.parse(b'{"hello": "world"}')

    assert 'smaller than document' in str(exc.value)
