import gc
import json
import sys
import weakref

import pytest

import simdjson


def test_parser_reuse(parser):
    old = parser.parse(b'{"deep":{"value":1},"array":[{"value":2}]}')
    current = parser.parse(b'{"deep":{"value":3}}')
    # Create descendants after reuse, then discard their parents too.
    child = old['deep']
    pointed = old.at_pointer('/array/0')
    array = old['array']
    del old, current
    parser.parse(b'[]')
    assert child.as_dict() == {'value': 1}
    assert pointed['value'] == 2
    assert array[0]['value'] == 2
    assert array.at_pointer('/0/value') == 2
    assert array[::-1] == [{'value': 2}]
    assert child.mini == b'{"value":1}'


def test_loop_variable_survives_reuse(parser):
    # Original #125: the loop variable remains after the other proxies die.
    for value in range(5):
        doc = parser.parse(json.dumps([{'value': value}, {'status': 'ok'}]))
        *results, status = doc
        for x in results:
            assert x['value'] == value
        del status, results, doc
    assert x['value'] == 4


@pytest.mark.parametrize('payload', [b'{"child":{"value":1}}', b'[{"value":1}]'])
def test_proxies_do_not_retain_parser(payload):
    parser = simdjson.Parser()
    ref = weakref.ref(parser)
    doc = parser.parse(payload)
    assert doc.parser is parser
    del parser
    gc.collect()
    assert ref() is None
    assert doc.parser is None
    # A new proxy created after parser destruction must still own the document.
    child = doc['child'] if isinstance(doc, simdjson.Object) else doc[0]
    del doc
    gc.collect()
    assert child.parser is None
    assert child.as_dict() == {'value': 1}


@pytest.mark.parametrize('method', ['keys', 'values', 'items'])
@pytest.mark.parametrize('started', [False, True])
def test_object_iterator_lifetime(method, started):
    parser = simdjson.Parser()
    doc = parser.parse(b'{"a":{"value":1},"b":[2]}')
    expected = list(getattr(doc, method)())
    iterator = getattr(doc, method)()
    prefix = [next(iterator)] if started else []
    del doc
    parser.parse(b'{"replacement":true}')
    del parser
    gc.collect()
    assert prefix + list(iterator) == expected


@pytest.mark.parametrize('started', [False, True])
def test_array_iterator_lifetime(started):
    parser = simdjson.Parser()
    doc = parser.parse(b'[{"value":1},{"value":2}]')
    iterator = iter(doc)
    prefix = [next(iterator)] if started else []
    del doc
    parser.parse(b'[0]')
    del parser
    gc.collect()
    assert [item.as_dict() for item in prefix + list(iterator)] == [
        {'value': 1}, {'value': 2}
    ]


def test_parse_failure_preserves_old_documents(parser):
    old = parser.parse(b'{"child":[1,2,3]}')
    for _ in range(3):
        with pytest.raises(ValueError):
            parser.parse(b'{"unfinished":[')
    assert parser.parse(b'[4]', recursive=True) == [4]
    assert old['child'].as_list() == [1, 2, 3]


def test_capacity_failure_preserves_old_document():
    parser = simdjson.Parser(max_capacity=64)
    old = parser.parse(b'{"value":1}')
    with pytest.raises(ValueError):
        parser.parse(b'["' + b'x' * 128 + b'"]')
    assert old['value'] == 1
    assert parser.parse(b'[2]', recursive=True) == [2]


def test_document_survives_capacity_growth(parser):
    old = parser.parse(b'{"value":"original"}')
    large = parser.parse(b'["' + b'x' * 100000 + b'"]')
    assert old['value'] == 'original'
    assert len(large[0]) == 100000
    assert parser.parse(b'null') is None
    assert old['value'] == 'original'


def test_reentrant_array_index(parser):
    old = parser.parse(b'[{"value":1}]')

    class Index:
        def __index__(self):
            parser.parse(b'[2,3,4]')
            return 0

    assert old[Index()]['value'] == 1


def test_buffer_export_survives_document_destruction():
    parser = simdjson.Parser()
    doc = parser.parse(b'[1,2,3]')
    buffer = memoryview(doc.as_buffer(of_type='i'))
    del doc, parser
    gc.collect()
    assert list(buffer.cast('q')) == [1, 2, 3]


def test_load_lifetime_and_failures(parser, tmp_path):
    path = tmp_path / 'document.json'
    path.write_bytes(b'{"value":[1,2]}')
    old = parser.load(path)
    path.write_bytes(b'{"value":[3,4]}')
    new = parser.load(path)
    path.write_bytes(b'{"unfinished":')
    with pytest.raises(ValueError):
        parser.load(path)
    path.unlink()
    with pytest.raises(IOError):
        parser.load(path)
    parser.parse(b'null')
    assert old['value'].as_list() == [1, 2]
    assert new['value'].as_list() == [3, 4]


def test_reentrant_path_conversion(parser, tmp_path):
    path = tmp_path / 'document.json'
    path.write_bytes(b'[2]')
    retained = []

    class Path:
        def __fspath__(self):
            retained.append(parser.parse(b'[1]'))
            return str(path)

    assert parser.load(Path()).as_list() == [2]
    assert retained[0].as_list() == [1]


@pytest.mark.skipif(sys.version_info < (3, 12), reason='Python buffer protocol')
def test_reentrant_buffer_conversion(parser):
    retained = []

    class Buffer:
        def __buffer__(self, flags):
            retained.append(parser.parse(b'[1]'))
            return memoryview(b'[2]')

        def __release_buffer__(self, view):
            retained.append(parser.parse(b'[3]'))

    doc = parser.parse(Buffer())
    assert doc.as_list() == [2]
    assert [value.as_list() for value in retained] == [[1], [3]]


def test_mutable_input_is_not_retained(parser):
    source = bytearray(b'{"value":"original"}')
    doc = parser.parse(source)
    source[:] = b'x'
    assert doc['value'] == 'original'


@pytest.mark.parametrize('length', [0, 1, 31, 32, 63, 64, 65, 127, 128, 4095, 4096])
@pytest.mark.parametrize('ending', [b'1', b'-1.25e30', b'true', b'null', b'"escaped\\n"'])
def test_unpadded_input_boundaries(parser, length, ending):
    payload = b' ' * length + ending
    assert parser.parse(payload, recursive=True) == json.loads(payload)
