"""Parser benchmarks, styled after the ones used by orjson."""
import platform
from json import loads as json_loads

import pytest

if platform.python_implementation() == 'PyPy':
    pytest.skip(
        'Skipping benchmarks on pypy, as orjson does not support it.',
        allow_module_level=True
    )

from orjson import loads as orjson_loads
from rapidjson import loads as rapidjson_loads
from simplejson import loads as simplejson_loads

import csimdjson


def csimdjson_loads(content):
    return csimdjson.Parser().parse(content)


@pytest.mark.slow
@pytest.mark.parametrize(
    ['group', 'func'],
    [
        ('csimdjson', csimdjson_loads),
        ('orjson', orjson_loads),
        ('rapidjson', rapidjson_loads),
        ('simplejson', simplejson_loads),
        ('json', json_loads)
    ]
)
@pytest.mark.parametrize(
    'path',
    [
        'jsonexamples/canada.json',
        'jsonexamples/twitter.json',
        'jsonexamples/github_events.json',
        'jsonexamples/citm_catalog.json',
        'jsonexamples/mesh.json'
    ]
)
def test_loads_json(group, func, path, benchmark):
    benchmark.group = '{path} deserialization'.format(path=path)
    benchmark.extra_info['group'] = group

    with open(path, 'rb') as src:
        content = src.read()
        benchmark(func, content)
