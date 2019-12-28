import json
import timeit

import pytest

import simdjson
from simdjson import ParsedJson, parse_query

@pytest.mark.slow
def test_speed_items(json_query_example):
    """Compare every example json file between ParsedJson.items and ParsedJson.items.
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

    items_time_with_parsed_query = sum(timeit.repeat(
        """pj.allocate_capacity(len(s));pj.parse(s);pj.items(query)""",
        setup="from simdjson import ParsedJson; pj=ParsedJson()",
        globals={
            'query': parse_query(query),
            's': file
        },
        number=number,
        repeat=repeat
    ))/repeat

    assert items_time_with_parsed_query < items_time, (
        'items_with_parsed_query slower than items, {} vs {}'
    ).format(
        items_time_with_parsed_query,
        items_time
    )
