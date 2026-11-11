import io
import json
from pathlib import Path

import pytest
import simdjson


@pytest.mark.parametrize('payload', [
    b'null', b'true', b'false', b'0', b'-1', b'1.5', b'-0.0',
    b'-9223372036854775808', b'9223372036854775808', b'18446744073709551615',
    b'"hello\\n\\u0000\\ud83d\\ude00"', b'[]', b'{}',
    b'{"a":1,"a":2,"a\\u0000b":{"\\u0061":[1,true,null]}}',
    b' [ {"x":[1,2.5,"text"]}, {}, [] ] \n', b'\xef\xbb\xbf[1]',
])
def test_eager_matches_dom(parser, payload):
    result = parser.parse(payload, recursive=True)
    lazy = parser.parse(payload)
    expected = lazy.as_dict() if isinstance(lazy, simdjson.Object) else (
        lazy.as_list() if isinstance(lazy, simdjson.Array) else lazy)
    assert result == expected
    assert type(result) is type(expected)
    assert simdjson.loads(payload) == expected
    assert simdjson.load(io.BytesIO(payload)) == expected


@pytest.mark.parametrize('payload', [
    b'', b' ', b'{} {}', b'[1] garbage', b'true false', b'1 2',
    b'NaN', b'Infinity', b'01', b'1e9999', b'18446744073709551616',
    b'-9223372036854775809', b'[1,,2]', b'{"a":1,}', b'"\\uD800"',
    b'{"ignored":[1,]}', b'{"a":1,"a":NaN}', b'[trueX]', b'nullX',
    b'"unterminated', b'"\xff"', b'[' * 1100 + b']' * 1100,
])
def test_eager_validates_entire_document(parser, payload):
    with pytest.raises(ValueError):
        parser.parse(payload, recursive=True)
    assert parser.parse(b'[1]', recursive=True) == [1]


def test_eager_corpus(parser, jsonexamples):
    directory = Path(jsonexamples) / 'test_parsing'
    for prefix in ('y', 'n'):
        files = sorted(directory.glob(prefix + '_*.json'))
        assert files
        for path in files:
            if prefix == 'y':
                parser.parse(path.read_bytes(), recursive=True)
            else:
                with pytest.raises(ValueError):
                    parser.parse(path.read_bytes(), recursive=True)


def test_eager_load_and_capacity(tmp_path):
    path = tmp_path / 'input.json'
    path.write_bytes(b'{"a":[1,2,3]}')
    parser = simdjson.Parser(max_capacity=64)
    assert parser.load(path, recursive=True) == {'a': [1, 2, 3]}
    path.write_bytes(b'[' + b'0,' * 100 + b'0]')
    with pytest.raises(ValueError):
        parser.load(path, recursive=True)
    with pytest.raises(ValueError):
        parser.parse(path.read_bytes(), recursive=True)
    path.write_bytes(b'[1] trailing')
    with pytest.raises(ValueError):
        parser.load(path, recursive=True)


@pytest.mark.parametrize('convert', [str, str.encode, lambda x: bytearray(x.encode()),
                                     lambda x: memoryview(x.encode())])
def test_eager_input_types(parser, convert):
    assert parser.parse(convert('{"value":[1]}'), recursive=True) == {'value': [1]}


def test_eager_and_streaming_implementations(parser):
    original = parser.implementation[0]
    payload = b'{"a\\u0000b":[true,null,"caf\\u00e9",18446744073709551615]}'
    expected = json.loads(payload)
    try:
        for name, _ in parser.get_implementations():
            parser.implementation = name
            assert parser.parse(payload, recursive=True) == expected
            assert list(parser.parse_many(payload + b'\n' + payload, batch_size=128)) == [expected, expected]
    finally:
        parser.implementation = original
