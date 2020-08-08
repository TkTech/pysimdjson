"""Parser benchmarks, styled after the ones used by orjson."""
import re
import json
import importlib

import pytest


# The files each benchmark will be run against.
TEST_FILES = [
    'jsonexamples/canada.json',
    'jsonexamples/twitter.json',
    'jsonexamples/github_events.json',
    'jsonexamples/citm_catalog.json',
    'jsonexamples/mesh.json',
    'jsonexamples/gsoc-2018.json'
]


def pytest_generate_tests(metafunc):
    # Only run the benchmarks against libraries we could actually find.
    # We tend to be a lot more portable than the alternatives, so we
    # sometimes can't compare. ex: orjson on PyPy.
    libs = [
        'json',
        'orjson',
        'rapidjson',
        'simplejson',
        'simdjson',
        'ujson'
    ]
    available = []

    for module in libs:
        try:
            i = importlib.import_module(module)
        except ImportError:
            continue

        available.append((module, i))

    metafunc.parametrize(
        ['group', 'module'],
        available,
        ids=[p[0] for p in available],
        scope='class'
    )
    metafunc.parametrize(
        'path',
        TEST_FILES,
        ids=[
            re.sub(r'jsonexamples/([^\.]*).json', r'{\1}', path)
            for path in TEST_FILES
        ],
        scope='class'
    )


def _deep(doc):
    # Find the deepest search path into `doc`.
    if isinstance(doc, list):
        d = dict((i, [i]) for i in range(len(doc)))
    else:
        d = dict((k, [k]) for k in doc.keys())

    for k in d:
        if isinstance(doc[k], dict):
            v = _deep(doc[k])
            if v:
                d[k].extend(v)
        elif isinstance(doc[k], list):
            v = _deep(doc[k])
            if v:
                d[k].extend(v)

    keys = sorted(d, key=lambda k: len(d[k]))
    if keys:
        return d[keys[-1]]

    return None


def _do_path(method, path, doc_content):
    # Navigate to `path` after loading `doc_content`.
    d = method(doc_content)
    for p in path:
        d = d[p]


@pytest.mark.slow
class TestBenchmarks:
    def test_loads(self, group, module, path, benchmark):
        """Test the complete loading of documents."""
        benchmark.group = '{path} deserialization'.format(path=path)
        benchmark.extra_info['group'] = group

        with open(path, 'rb') as src:
            content = src.read()

        benchmark(getattr(module, 'loads'), content)

    def test_deepest_key(self, group, module, path, benchmark):
        """Test how quickly we can access the deepest key."""
        benchmark.group = '{path} deepest key'.format(path=path)
        benchmark.extra_info['group'] = group

        with open(path, 'rb') as src:
            content = src.read()

        # We don't want to use loads() for us since that recursively uplifts
        # instead of using proxies.
        if group == 'simdjson':
            p = getattr(module, 'Parser')()
            method = p.parse
        else:
            method = getattr(module, 'loads')

        # Find the deepest key we can in any source file.
        doc = json.loads(content)

        if not isinstance(doc, (dict, list)):
            pytest.skip(
                'Skipping a benchmark file that does not contain a dict.'
            )

        benchmark(_do_path, method, _deep(doc), content)
