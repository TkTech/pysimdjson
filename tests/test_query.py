import pytest

from simdjson import parse_query, ParsedJson

def test_parse_query_get():
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


def test_parse_query_array():
    assert parse_query('."test"[]') == [
        (10, b'test'),
        (20, None)
    ]

    assert parse_query('.[]') == [
        (10, b''),
        (20, None)
    ]

    # Closing bracket without an opening.
    with pytest.raises(ValueError):
        parse_query(']')


def test_items():
    doc = b'{"simple": 1}'

    pj = ParsedJson(doc)

    assert pj.items('.') == {"simple": 1}

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

    assert pj.items('.results[0]')

def test_pre_parsed_query_items():
    doc = b'{"simple": 1}'

    pj = ParsedJson(doc)

    parsed_query = parse_query('.')
    assert pj.items(parsed_query) == {"simple": 1}

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

    parsed_query = parse_query('.count')
    assert pj.items(parsed_query) == 2
    parsed_query = parse_query('.results')
    assert pj.items(parsed_query) == [
        {'name': 'result_a'},
        {'name': 'result_b'}
    ]
    parsed_query = parse_query('.results[].name')
    assert pj.items(parsed_query) == [
        'result_a',
        'result_b'
    ]

    parsed_query = parse_query('.error.message')
    assert pj.items(parsed_query) == 'All good captain'

    parsed_query = parse_query('.results[0]')
    assert pj.items(parsed_query)
