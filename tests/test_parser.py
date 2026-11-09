import io
import pathlib
import os.path

import pytest

import simdjson


def test_load_str(parser, jsonexamples):
    """Ensure we can load a file from disk using a string."""
    with pytest.raises(ValueError):
        parser.load(os.path.join(jsonexamples, 'invalid.json'))

    doc = parser.load(os.path.join(jsonexamples, 'small', 'demo.json'))
    doc.at_pointer('/Image/Width')


def test_load_path(parser, jsonexamples):
    """Ensure we can load a file using a Path object."""
    doc = parser.load(pathlib.Path(jsonexamples) / 'small' / 'demo.json')
    doc.at_pointer('/Image/Width')


def test_parse_bytes(parser):
    """Ensure we can load from byte string fragments."""
    doc = parser.parse(b'{"hello": "world"}')
    assert doc.as_dict() == {'hello': 'world'}


@pytest.mark.parametrize('as_bytes', [False, True])
def test_load_pathlike(parser, tmp_path, as_bytes):
    path = tmp_path / 'document.json'
    path.write_text('{"hello": "world"}', encoding='utf-8')

    class CustomPath:
        def __fspath__(self):
            return os.fsencode(path) if as_bytes else str(path)

    assert parser.load(CustomPath(), recursive=True) == {'hello': 'world'}


def test_load_bytes(parser, tmp_path):
    path = tmp_path / 'document.json'
    path.write_text('[1, 2]', encoding='utf-8')
    assert parser.load(os.fsencode(path), recursive=True) == [1, 2]


def test_load_invalid_pathlike(parser):
    class InvalidPath:
        def __fspath__(self):
            return 123

    with pytest.raises(TypeError):
        parser.load(InvalidPath())


@pytest.mark.parametrize('src', [
    b'123456789012345678901234567890',
    b'[' * 1101 + b']' * 1101,
    b'{"unfinished": [1, 2',
    b'{} {}',
])
def test_parser_errors_are_value_errors(parser, src):
    with pytest.raises(ValueError):
        parser.parse(src)


def test_parse_str(parser):
    """Ensure we can load from string fragments."""
    doc = parser.parse('{"hello": "world"}')
    assert doc.as_dict() == {'hello': 'world'}


def test_parse_empty_buffer(parser):
    """Ensure trying to parse an empty buffer returns an error consistent
    with attempting to parse an empty bytestring."""
    # Issue #81
    with pytest.raises(ValueError) as bytes_exc:
        parser.parse(b'')

    with pytest.raises(ValueError) as buffer_exc:
        parser.parse(io.BytesIO(b'').getbuffer())

    assert str(bytes_exc.value) == str(buffer_exc.value)


def test_unicode_decode_error(parser, jsonexamples):
    """Ensure the parser raises encoding issues."""
    # Not all implementations are equal. When using the byte-by-byte fallback
    # Implementation, a ValueError will be raised for improper tape structure.
    # When using most (all?) other implementations, the expected
    # UnicodeDecodeError will be raised instead.
    with pytest.raises((UnicodeDecodeError, ValueError)):
        parser.load(
            os.path.join(
                jsonexamples,
                'test_parsing',
                'n_array_invalid_utf8.json'
            )
        )


def test_implementation():
    """Ensure we can set, get, and list the Implementation."""
    parser = simdjson.Parser()
    # Ensure a rubbish Implementation does not get set - simdjson does not do
    # a safety check, buy pysimdjson does. A break in this check will cause
    # a segfault.
    with pytest.raises(ValueError):
        parser.implementation = 'rubbish'

    implementations = [imp[0] for imp in parser.get_implementations()]
    assert 'fallback' in implementations
    original = parser.implementation[0]
    try:
        for implementation in implementations:
            parser.implementation = implementation
            assert parser.parse(b'{"hello": "world"}', recursive=True) == {
                'hello': 'world'
            }
            assert parser.implementation[0] == implementation
    finally:
        parser.implementation = original
