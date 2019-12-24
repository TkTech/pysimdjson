import json
import timeit

import pytest

import simdjson
from simdjson import ParsedJson, parse_query

@pytest.mark.slow
def test_speed_items(json_query_example):
    """Compare every example json file between ParsedJson.items and ParsedJson.items_from_parsed_query.
    """
    file_name, file, query = json_query_example

    number=10000
    repeat=3
    items_time = sum(timeit.repeat(
        """pj.allocate_capacity(len(s));pj.parse(s);pj.items(query)""",
        setup="from simdjson import ParsedJson; pj=ParsedJson()",
        globals={
            'query': query,
            's': file
        },
        number=number,
        repeat=repeat
    ))/repeat

    items_from_parsed_query_time = sum(timeit.repeat(
        """pj.allocate_capacity(len(s));pj.parse(s);pj.items_from_parsed_query(query)""",
        setup="from simdjson import ParsedJson; pj=ParsedJson()",
        globals={
            'query': parse_query(query),
            's': file
        },
        number=number,
        repeat=repeat
    ))/repeat

    assert items_from_parsed_query_time < items_time, (
        'items_from_parsed_query slower than items_time, {} vs {}'
    ).format(
        items_from_parsed_query_time,
        items_time
    )
