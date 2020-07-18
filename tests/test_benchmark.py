"""Parser benchmarks, styled after the ones used by orjson."""
import re
import importlib

import pytest


# The files each benchmark will be run against.
TEST_FILES = [
    'jsonexamples/canada.json',
    'jsonexamples/twitter.json',
    'jsonexamples/github_events.json',
    'jsonexamples/citm_catalog.json',
    'jsonexamples/mesh.json'
]


def pytest_generate_tests(metafunc):
    # Only run the benchmarks against libraries we could actually find.
    # We tend to be a lot more portable than the alternatives, so we
    # sometimes can't compare. ex: orjson on PyPy.
    libs = ['json', 'orjson', 'rapidjson', 'simplejson', 'simdjson']
    available = []

    for module in libs:
        try:
            i = importlib.import_module(module)
        except Exception as e:
            # Pre py3.6, ModuleImportError does not exist as a builtin.
            if e.__class__.__name__ in ('ModuleImportError', 'ImportError'):
                continue
            raise

        available.append((module, getattr(i, 'loads')))

    metafunc.parametrize(
        ['group', 'func'],
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


@pytest.mark.slow
class TestBenchmarks:
    def test_loads(self, group, func, path, benchmark):
        """Test the complete loading of documents."""
        benchmark.group = '{path} deserialization'.format(path=path)
        benchmark.extra_info['group'] = group

        with open(path, 'rb') as src:
            content = src.read()

        benchmark(func, content)
