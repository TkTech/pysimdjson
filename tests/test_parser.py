import pathlib

import pytest

import simdjson


def test_load(parser):
    """Ensure we can load from disk."""
    with pytest.raises(ValueError):
        parser.load('jsonexamples/invalid.json')

    doc = parser.load("jsonexamples/small/demo.json")
    doc.at_pointer('/Image/Width')

    doc = parser.load(pathlib.Path('jsonexamples') / 'small' / 'demo.json')
    doc.at_pointer('/Image/Width')


def test_parse_bytes(parser):
    """Ensure we can load from byte string fragments."""
    doc = parser.parse(b'{"hello": "world"}')
    assert doc.as_dict() == {'hello': 'world'}


def test_parse_str(parser):
    """Ensure we can load from string fragments."""
    doc = parser.parse('{"hello": "world"}')
    assert doc.as_dict() == {'hello': 'world'}


def test_unicode_decode_error(parser):
    """Ensure the parser raises encoding issues."""
    with pytest.raises(UnicodeDecodeError):
        parser.load('jsonexamples/test_parsing/n_array_invalid_utf8.json')


def test_implementation():
    """Ensure we can set, get, and list the implementation."""
    parser = simdjson.Parser()
    # Ensure a rubbish implementation does not get set - simdjson does not do
    # a safety check, buy pysimdjson does. A break in this check will cause
    # a segfault.
    with pytest.raises(ValueError):
        parser.implementation = 'rubbish'

    # The generic, always-available implementation.
    parser.implementation = 'fallback'
    parser.parse(b'{"hello": "world"}')

    assert parser.implementation[0] == 'fallback'

    implementations = [imp[0] for imp in parser.implementations]
    assert 'fallback' in implementations
