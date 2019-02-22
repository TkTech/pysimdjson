import glob

import pytest

def pytest_addoption(parser):
    parser.addoption(
        '--runslow',
        default=False,
        action='store_true',
        help='run slow tests'
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption('--runslow'):
        return

    skip_slow = pytest.mark.skip(reason='need --runslow option to run')
    for item in items:
        if 'slow' in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(scope='module', params=glob.glob('jsonexamples/**.json'))
def json_example(request):
    with open(request.param, 'rb') as fin:
        yield (request.param, fin.read())
