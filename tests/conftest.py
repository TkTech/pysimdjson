import os.path
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        '--runslow',
        action='store_true',
        default=False,
        help='run slow tests'
    )


def pytest_configure(config):
    config.addinivalue_line('markers', 'slow: mark test as slow to run')


def pytest_collection_modifyitems(config, items):
    if config.getoption('--runslow'):
        # --runslow given in cli: do not skip slow tests
        return

    skip_slow = pytest.mark.skip(reason='need --runslow option to run')
    for item in items:
        if 'slow' in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
def parser():
    import csimdjson
    yield csimdjson.Parser()


@pytest.fixture
def doc(parser):
    yield parser.parse(b'''{
        "array": [1, 2, 3],
        "object": {"hello": "world"},
        "int64": -1,
        "uint64": 18446744073709551615,
        "double": 1.1,
        "string": "test",
        "bool": true,
        "null_value": null
    }''')


@pytest.fixture
def parsing_tests():
    return {
        'y': (Path('jsonexamples') / 'test_parsing').glob('y_*.json'),
        'n': (Path('jsonexamples') / 'test_parsing').glob('n_*.json'),
        'i': (Path('jsonexamples') / 'test_parsing').glob('i_*.json')
    }


@pytest.fixture
def jsonexamples():
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..',
            'jsonexamples'
        )
    )
