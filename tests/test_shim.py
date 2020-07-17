import json
import simdjson


def test_load():
    """Ensure basic usage of load is the same."""
    with open('jsonexamples/canada.json', 'rb') as fin:
        builtin_json = json.load(fin)

    with open('jsonexamples/canada.json', 'rb') as fin:
        simd_json = simdjson.load(fin)

    assert builtin_json == simd_json


def test_loads():
    """Ensure basic usage of loads is the same."""
    with open('jsonexamples/canada.json', 'rb') as fin:
        content = fin.read()

    assert json.loads(content) == simdjson.loads(content)
