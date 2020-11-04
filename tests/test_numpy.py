import json

import pytest

import simdjson


def with_buffer(content):
    import numpy

    parser = simdjson.Parser()
    doc = parser.parse(content)
    assert len(numpy.frombuffer(doc.as_buffer(of_type='d'))) == 10001


def without_buffer(content):
    import numpy

    parser = simdjson.Parser()
    doc = parser.parse(content)
    assert len(numpy.array(doc.as_list())) == 10001


def with_builtin(content):
    import numpy
    assert len(numpy.array(json.loads(content))) == 10001


def with_orjson(content):
    import numpy
    import orjson

    assert len(numpy.array(orjson.loads(content))) == 10001


@pytest.mark.slow
@pytest.mark.parametrize('loader', [
    with_buffer, without_buffer, with_builtin, with_orjson])
def test_array_to_numpy(benchmark, loader):
    """Test how quickly we can load a homogeneous array of floats into a
    numpy array."""
    with open('jsonexamples/numbers.json', 'rb') as src:
        content = src.read()

    benchmark.group = 'numpy array (deserialize)'
    benchmark.extra_info['group'] = 'numpy'
    benchmark(loader, content)
