import json
import simdjson


def _test_load():
    """Ensure basic usage of load is the same."""
    # We don't use a binary file here because pre-py3.6 the built-in couldn't
    # handle bytes.
    with open('jsonexamples/canada.json', 'r') as fin:
        builtin_json = json.load(fin)

    with open('jsonexamples/canada.json', 'rb') as fin:
        simd_json = simdjson.load(fin)

    assert builtin_json == simd_json


def _test_loads():
    """Ensure basic usage of loads is the same."""
    # We don't use a binary file here because pre-py3.6 the built-in couldn't
    # handle bytes.
    with open('jsonexamples/canada.json', 'r') as fin:
        content = fin.read()

    assert json.loads(content) == simdjson.loads(content)
