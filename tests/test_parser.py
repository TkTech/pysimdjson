import pytest

import csimdjson


def test_load(parser):
    """Ensure we can load from disk."""
    with pytest.raises(csimdjson.SimdjsonError):
        parser.load('jsonexamples/invalid.json')

    doc = parser.load("jsonexamples/small/demo.json")
    doc.at('Image/Width')


def test_parse(parser):
    """Ensure we can load from string fragments."""
    parser.parse('{"hello": "world"}')
