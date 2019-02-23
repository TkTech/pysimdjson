import pytest

from pysimdjson import parse_query, ParsedJson

def test_parse_query():
    # Simple unquoted string with a delimiter.
    assert parse_query('.test.string') == [
        (10, b'test'),
        (10, b'string')
    ]
    # Quoted string with an escaped quote within it.
    assert parse_query('."t\\"t"') == [
        (10, b't"t')
    ]
    # Quoted string followed by delimiter and unquoted string.
    assert parse_query('."test".string') == [
        (10, b'test'),
        (10, b'string')
    ]

    assert parse_query('."test"[]') == [
        (10, b'test'),
        (20, b'')
    ]

    assert parse_query('.[]') == [
        (10, b''),
        (20, b'')
    ]

    # Closing bracket without an opening.
    with pytest.raises(ValueError):
        parse_query(']')


def test_items():
    doc = b'''{
        "count": 2,
        "results": [
            {"name": "result_a"},
            {"name": "result_b"}
        ],
        "error": {
            "message": "All good captain"
        }
    }'''

    pj = ParsedJson(doc)

    assert pj.items('.count') == 2
    assert pj.items('.results') == [
        {'name': 'result_a'},
        {'name': 'result_b'}
    ]
    assert pj.items('.results[].name') == [
        'result_a',
        'result_b'
    ]
    assert pj.items('.error.message') == 'All good captain'
