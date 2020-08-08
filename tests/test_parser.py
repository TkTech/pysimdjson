import pytest


def test_load(parser):
    """Ensure we can load from disk."""
    with pytest.raises(ValueError):
        parser.load('jsonexamples/invalid.json')

    doc = parser.load("jsonexamples/small/demo.json")
    doc.at('Image/Width')


def test_parse(parser):
    """Ensure we can load from string fragments."""
    parser.parse(b'{"hello": "world"}')


def test_unicode_decode_error(parser):
    """Ensure the parser raises encoding issues."""
    with pytest.raises(UnicodeDecodeError):
        parser.load('jsonexamples/test_parsing/n_array_invalid_utf8.json')
