import json
import timeit

import pytest

import simdjson


@pytest.mark.slow
def test_speed_loads(json_example):
    """Compare every example json file between simdjson and the built-in JSON module.

    Ideally, every file will parse signficantly faster under simdjson.

    .. note::

        This is very trivial test, and the results of a single run over such a
        low number should not be used as any sort of benchmark. This is a
        simple test just for debugging purposes.
    """
    file_name, file = json_example

    simd_time = timeit.timeit(
        'json.loads(s)',
        globals={
            'json': simdjson,
            's': file
        },
        number=100
    )

    json_time = timeit.timeit(
        'json.loads(s)',
        globals={
            'json': json,
            's': file
        },
        number=100
    )

    assert simd_time < json_time, (
        'simdjson version slower then built-in, {} vs {}'
    ).format(
        simd_time,
        json_time
    )

