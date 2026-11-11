import json
import os.path
import simdjson


def test_load(jsonexamples):
    """Ensure basic usage of load is the same."""
    path = os.path.join(jsonexamples, 'canada.json')
    with open(path, 'r', encoding='utf-8') as fin:
        builtin_json = json.load(fin)

    with open(path, 'rb') as fin:
        simd_json = simdjson.load(fin)

    assert builtin_json == simd_json


def test_loads(jsonexamples):
    """Ensure basic usage of loads is the same."""
    with open(os.path.join(jsonexamples, 'canada.json'), 'r', encoding='utf-8') as fin:
        content = fin.read()

    assert json.loads(content) == simdjson.loads(content)


def test_public_exports():
    import csimdjson

    assert simdjson.VERSION == csimdjson.VERSION
    namespace = {}
    exec('from simdjson import *', namespace)
    assert {name for name in namespace if name != '__builtins__'} == set(simdjson.__all__)
    assert namespace['loads']('{"a": 1}') == {'a': 1}
