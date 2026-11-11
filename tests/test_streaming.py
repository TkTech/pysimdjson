import io
import json
import weakref
import gc

import pytest
import simdjson


@pytest.fixture(params=['parse_many', 'load_many'])
def ndjson_stream(request):
    def make_stream(payload, **kwargs):
        if request.param == 'load_many':
            return simdjson.load_many(io.BytesIO(payload), **kwargs)
        return simdjson.parse_many(payload, **kwargs)
    return make_stream


@pytest.mark.parametrize('newline', [b'\n', b'\r\n'])
@pytest.mark.parametrize('final_newline', [False, True])
@pytest.mark.parametrize('batch_size', [32, 33, 63, 64, 65])
def test_ndjson_line_boundaries(ndjson_stream, newline, final_newline, batch_size):
    values = [{}, [], 'escaped\nnewline', 'quote" and \\', 1.5, None, True, False]
    lines = [b' \t', b'']
    for value in values:
        lines.extend([b' \t' + json.dumps(value).encode() + b'\t ', b''])
    payload = newline.join(lines[:-1]) + (newline if final_newline else b'')
    assert list(ndjson_stream(payload, batch_size=batch_size)) == values


@pytest.mark.parametrize('payload', [
    b'{} {}', b'{}{}', b'[]\t[]', b'1 2', b'"a" "b"', b'true false',
    b'null\rnull', b'{} junk', b'{}\x00',
    b'[\n1\n]', b'{\r\n"a": 1\r\n}', b'{"a":\n[]}', b'[1,\n2]',
    b'[1]' + b' ' * 60 + b'[2]',
])
@pytest.mark.parametrize('batch_size', [32, 128])
def test_ndjson_rejects_invalid_lines(ndjson_stream, payload, batch_size):
    with ndjson_stream(payload, batch_size=batch_size) as stream:
        with pytest.raises(ValueError):
            # Do not yield even the first value of an invalid line.
            next(stream)
        assert stream.closed


def test_ndjson_invalid_later_line(ndjson_stream):
    with ndjson_stream(b'[0]\n[1] [2]\n[3]') as stream:
        assert next(stream) == [0]
        with pytest.raises(ValueError, match='one JSON value per line'):
            next(stream)
        assert stream.closed


@pytest.mark.parametrize('read_size', [1, 2, 3, 7, 31])
def test_ndjson_short_file_reads(read_size):
    class Reader(io.BytesIO):
        def read(self, size):
            return super().read(min(size, read_size))

    payload = b'\xef\xbb\xbf\r\n {"a": 1}\r\n\n[2]\ntrue'
    assert list(simdjson.load_many(Reader(payload), batch_size=32)) == [{'a': 1}, [2], True]
    for payload in (b'[1] [2]\n', b'[\n1\n]\n'):
        with pytest.raises(ValueError):
            list(simdjson.load_many(Reader(payload), batch_size=32))


@pytest.mark.parametrize('batch_size', [32, 64, 65])
@pytest.mark.parametrize('ending', [b'', b'\n', b'\r\n'])
def test_record_size_boundaries(ndjson_stream, batch_size, ending):
    # Exercise every alignment, including a record that exactly fills a native
    # batch and a CRLF split between two file reads.
    for length in (batch_size - 1, batch_size, batch_size + 1):
        records = [b'"' + b'x' * (length - 2) + b'"',
                   b'[' + b' ' * (length - 3) + b'0]']
        for record in records:
            for offset in range(batch_size):
                payload = b'\n' * offset + record + ending
                with ndjson_stream(payload, batch_size=batch_size) as stream:
                    if length < batch_size:
                        assert list(stream) == [json.loads(record)]
                    else:
                        with pytest.raises(ValueError):
                            list(stream)
                    assert stream.closed


@pytest.mark.parametrize('read_size', [1, 2, 3, 7, 31, 64])
def test_record_size_with_bom_and_short_reads(read_size):
    class Reader(io.BytesIO):
        def read(self, size):
            assert size <= 64
            return super().read(min(size, read_size))

    for length in (63, 64, 65):
        # Count encoded bytes, including when a read splits a UTF-8 character.
        record = b'"' + b'\xc3\xa9' * ((length - 2) // 2) + b'x' * (length % 2) + b'"'
        assert len(record) == length
        for ending in (b'', b'\n', b'\r\n'):
            for prefix in (b'\xef\xbb\xbf', b'\xef\xbb\xbf\n', b'\n'):
                payload = prefix + record + ending
                for stream in (simdjson.parse_many(payload, batch_size=64),
                               simdjson.load_many(Reader(payload), batch_size=64)):
                    with stream:
                        if length < 64:
                            assert list(stream) == [json.loads(record)]
                        else:
                            with pytest.raises(ValueError):
                                list(stream)


@pytest.mark.parametrize('ending', [b'', b'\n', b'\r\n'])
def test_record_size_counts_surrounding_whitespace(ndjson_stream, ending):
    for length in (63, 64, 65, 257):
        for padding in ((length - 1, 0), (0, length - 1), (length // 2, length - 1 - length // 2)):
            record = b' ' * padding[0] + b'0' + b'\t' * padding[1]
            with ndjson_stream(record + ending, batch_size=64) as stream:
                if length < 64:
                    assert list(stream) == [0]
                else:
                    with pytest.raises(ValueError):
                        list(stream)


def test_long_blank_lines_followed_by_record_with_short_reads():
    class Reader(io.BytesIO):
        def read(self, size):
            return super().read(min(size, 7))

    for prefix in (b'', b'\xef\xbb\xbf'):
        blank = b' \t\r' * 200
        assert list(simdjson.load_many(Reader(prefix + blank + b'\n0\r\n'), batch_size=64)) == [0]
        # Discarding a long blank prefix must not erase its contribution to the
        # size of a record that starts later on that same line.
        with pytest.raises(ValueError):
            list(simdjson.load_many(Reader(prefix + blank + b'0\r\n'), batch_size=64))


def test_record_boundaries_with_max_capacity_and_implementations(parser):
    api = simdjson.Parser(max_capacity=64)
    record = b'"' + b'x' * 61 + b'"'
    payload = b'\n' + (record + b'\r\n') * 10 + record
    original = parser.implementation[0]
    try:
        for name, _ in parser.get_implementations():
            parser.implementation = name
            assert list(api.parse_many(payload, batch_size=64)) == ['x' * 61] * 11
            assert list(api.load_many(io.BytesIO(payload), batch_size=64)) == ['x' * 61] * 11
    finally:
        parser.implementation = original


@pytest.mark.parametrize('payload', [b'', b' \n\t', b'\n\n'])
def test_empty_stream(payload):
    assert list(simdjson.parse_many(payload, batch_size=64)) == []
    assert list(simdjson.load_many(io.BytesIO(payload), batch_size=64)) == []


def test_stream_values_and_batches():
    values = [{'value': [i, '\x00é']} for i in range(100)]
    values += [None, True, False, 1.5, 'text', 2**64 - 1, [], {}]
    payload = '\n'.join(json.dumps(v) for v in values).encode()
    assert list(simdjson.parse_many(payload, batch_size=128)) == values
    assert list(simdjson.load_many(io.BytesIO(payload), batch_size=128)) == values


def test_stream_results_survive_parser_and_advancement():
    parser = simdjson.Parser()
    ref = weakref.ref(parser)
    stream = parser.parse_many(b'{"a":[1]}\n{"a":[2]}')
    del parser
    gc.collect()
    assert ref() is None
    first = next(stream)
    assert next(stream) == {'a': [2]}
    stream.close()
    assert first == {'a': [1]}
    assert list(stream) == []


def test_interleaved_streams(parser):
    a = parser.parse_many(b'[1]\n[2]')
    b = parser.parse_many(b'[3]\n[4]')
    old = parser.parse(b'{"old":1}')
    assert next(a) == [1]
    assert next(b) == [3]
    assert parser.parse(b'[5]', recursive=True) == [5]
    assert next(a) == [2]
    assert next(b) == [4]
    assert old['old'] == 1


@pytest.mark.parametrize('suffix', [b'{', b'"unfinished', b'[1,', b'{"a":NaN}',
                                  b'[1,,2]', b'01', b'"\xff"', b'{"a":1,}'])
@pytest.mark.parametrize('file_mode', [False, True])
def test_stream_malformed_tail(suffix, file_mode):
    payload = b'{"ok":1}\n' + suffix
    stream = simdjson.load_many(io.BytesIO(payload), batch_size=64) if file_mode else (
        simdjson.parse_many(payload, batch_size=64))
    with pytest.raises(ValueError):
        list(stream)
    assert list(stream) == []


def test_file_chunk_boundaries_and_newline_variants():
    values = [{'a': i} for i in range(50)]
    for newline in (b'\n', b'\r\n'):
        for final_newline in (b'', newline):
            payload = newline.join(json.dumps(v).encode() for v in values) + final_newline
            for size in (32, 33, 63, 64, 65):
                assert list(simdjson.load_many(io.BytesIO(payload), batch_size=size)) == values


def test_files_closed_on_early_exit(tmp_path):
    path = tmp_path / 'records.ndjson'
    path.write_bytes(b'[1]\n[2]\n')
    with simdjson.load_many(path, batch_size=32) as stream:
        assert next(stream) == [1]
    path.unlink()
    caller_file = io.BytesIO(b'[1]\n[2]\n')
    stream = simdjson.load_many(caller_file, batch_size=32)
    assert next(stream) == [1]
    stream.close()
    assert not caller_file.closed


@pytest.mark.parametrize('size', [0, -1, 31, 2**100, 1.5, '64'])
def test_invalid_batch_size(size):
    with pytest.raises((TypeError, ValueError, OverflowError)):
        simdjson.parse_many(b'', batch_size=size)
    with pytest.raises((TypeError, ValueError, OverflowError)):
        simdjson.load_many(io.BytesIO(), batch_size=size)


def test_oversized_records():
    payload = b'"' + b'x' * 200 + b'"\n'
    with pytest.raises(ValueError):
        list(simdjson.parse_many(payload, batch_size=64))
    with pytest.raises(ValueError):
        list(simdjson.load_many(io.BytesIO(payload), batch_size=64))
    assert list(simdjson.load_many(io.BytesIO(payload), batch_size=256)) == ['x' * 200]
    with pytest.raises(ValueError):
        simdjson.Parser(max_capacity=64).parse_many(b'1', batch_size=128)


def test_bounded_reads():
    class Reader(io.BytesIO):
        def read(self, size=-1):
            assert 0 < size <= 64
            return super().read(size)
    values = list(range(1000))
    data = b'\n'.join(str(v).encode() for v in values)
    assert list(simdjson.load_many(Reader(data), batch_size=64)) == values


def test_mutable_stream_input_is_snapshotted():
    data = bytearray(b'[1]\n[2]')
    stream = simdjson.parse_many(data)
    data[:] = b'garbage'
    assert list(stream) == [[1], [2]]


def test_load_many_rejects_text_files():
    with pytest.raises(TypeError):
        list(simdjson.load_many(io.StringIO('{}\n')))


def test_large_blank_lines(ndjson_stream):
    data = b' ' * 200 + b'\n[1]\n' + b'\t' * 200
    assert list(ndjson_stream(data, batch_size=64)) == [[1]]


def test_bom_only_at_start(ndjson_stream):
    assert list(ndjson_stream(b'\xef\xbb\xbf[1]\n', batch_size=32)) == [[1]]
    payload = b'[1]\n' + b' ' * 28 + b'\xef\xbb\xbf[2]\n'
    with pytest.raises(ValueError):
        list(ndjson_stream(payload, batch_size=32))


def test_empty_memoryview():
    assert list(simdjson.parse_many(memoryview(b''))) == []


@pytest.mark.parametrize('file_mode', [False, True])
@pytest.mark.parametrize('on_parser', [False, True])
def test_stream_context_manager(file_mode, on_parser):
    api = simdjson.Parser() if on_parser else simdjson
    payload = b'{"a":[1]}\n{"a":[2]}\n'
    stream = api.load_many(io.BytesIO(payload)) if file_mode else api.parse_many(payload)
    assert isinstance(stream, simdjson.DocumentStream)
    assert iter(stream) is stream
    assert not stream.closed
    with stream as entered:
        assert entered is stream
        first = next(stream)
    assert first == {'a': [1]}
    assert stream.closed
    stream.close()
    stream.close()
    assert list(stream) == []
    with pytest.raises(ValueError, match='closed'):
        with stream:
            pass


@pytest.mark.parametrize('file_mode', [False, True])
def test_context_preserves_body_exception(file_mode):
    payload = b'[1]\n[2]\n'
    stream = simdjson.load_many(io.BytesIO(payload)) if file_mode else simdjson.parse_many(payload)
    error = RuntimeError('consumer failed')
    with pytest.raises(RuntimeError) as caught:
        with stream:
            assert next(stream) == [1]
            raise error
    assert caught.value is error
    assert stream.closed


@pytest.mark.parametrize('file_mode', [False, True])
@pytest.mark.parametrize('payload', [b'', b'[1]\n[2]\n'])
def test_exhaustion_closes_stream(file_mode, payload):
    source = io.BytesIO(payload)
    stream = simdjson.load_many(source) if file_mode else simdjson.parse_many(payload)
    with stream:
        assert list(stream) == ([] if not payload else [[1], [2]])
        assert stream.closed
    assert not source.closed


@pytest.mark.parametrize('finish', ['exhaust', 'early', 'body_error', 'parse_error'])
def test_owned_file_lifetime(tmp_path, finish):
    path = tmp_path / 'records.ndjson'
    path.write_bytes(b'[1]\n[2]\n' if finish != 'parse_error' else b'[1]\n{')
    opened = []

    def open_readers():
        return [obj for obj in gc.get_objects()
                if isinstance(obj, io.BufferedReader) and obj.name == str(path)]

    stream = simdjson.load_many(path)
    assert not open_readers()

    def consume():
        with stream:
            assert not open_readers()  # entering does not open the file
            assert next(stream) == [1]
            opened.extend(open_readers())
            assert len(opened) == 1
            if finish == 'body_error':
                raise RuntimeError('consumer failed')
            if finish in ('exhaust', 'parse_error'):
                assert list(stream) == [[2]]

    if finish == 'body_error':
        with pytest.raises(RuntimeError, match='consumer failed'):
            consume()
    elif finish == 'parse_error':
        with pytest.raises(ValueError):
            consume()
    else:
        consume()
    # Keep a reference to the actual file to verify explicit closure rather
    # than relying on garbage collection or unlink succeeding on Unix.
    assert opened[0].closed
    assert stream.closed


def test_close_before_file_is_opened(tmp_path):
    stream = simdjson.load_many(tmp_path / 'missing.ndjson')
    with stream:
        pass
    assert stream.closed
    assert list(stream) == []


def test_file_reader_cannot_reenter_stream():
    class Reader(io.BytesIO):
        def read(self, size):
            with pytest.raises(RuntimeError, match='executing'):
                next(stream)
            with pytest.raises(RuntimeError, match='executing'):
                stream.close()
            return super().read(size)

    source = Reader(b'[1]\n[2]\n')
    with simdjson.load_many(source) as stream:
        assert list(stream) == [[1], [2]]
    assert stream.closed
    assert not source.closed


def test_file_open_failure_closes_stream(tmp_path):
    stream = simdjson.load_many(tmp_path / 'missing.ndjson')
    with pytest.raises(FileNotFoundError):
        with stream:
            next(stream)
    assert stream.closed
