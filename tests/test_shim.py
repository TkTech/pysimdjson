import json
import os.path

import simdjson


def test_load(jsonexamples):
    """Ensure basic usage of load is the same."""
    # We don't use a binary file here because pre-py3.6 the built-in couldn't
    # handle bytes.
    path = os.path.join(jsonexamples, 'canada.json')

    with open(path, 'r') as fin:
        builtin_json = json.load(fin)

    with open(path, 'rb') as fin:
        simd_json = simdjson.load(fin)

    assert builtin_json == simd_json


def test_loads(jsonexamples):
    """Ensure basic usage of loads is the same."""
    # We don't use a binary file here because pre-py3.6 the built-in couldn't
    # handle bytes.
    with open(os.path.join(jsonexamples, 'canada.json'), 'r') as fin:
        content = fin.read()

    assert json.loads(content) == simdjson.loads(content)
