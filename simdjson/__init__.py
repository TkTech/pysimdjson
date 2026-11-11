"""High-level bindings for the simdjson project."""
import json

try:
    from csimdjson import (
        Parser,
        Array,
        Object,
        DocumentStream,
        MAXSIZE_BYTES,
        PADDING,
        VERSION
    )
except ImportError:
    raise RuntimeError('Unable to import low-level simdjson bindings.')

__all__ = [
    'Parser',
    'Array',
    'Object',
    'DocumentStream',
    'MAXSIZE_BYTES',
    'PADDING',
    'VERSION',
    'load',
    'loads',
    'parse_many',
    'load_many',
    'dump',
    'dumps',
    'JSONEncoder',
]


def load(fp, *, cls=None, object_hook=None, parse_float=None, parse_int=None,
         parse_constant=None, object_pairs_hook=None, **kwargs):
    """
    Parse the JSON document in the file-like object fp and return the parsed
    object.

    All other arguments are ignored, and are provided only for compatibility
    with the built-in json module.
    """
    parser = Parser()
    return parser.parse(fp.read(), True)


def loads(s, *, cls=None, object_hook=None, parse_float=None, parse_int=None,
          parse_constant=None, object_pairs_hook=None, **kwargs):
    """
    Parse the JSON document s and return the parsed object.

    All other arguments are ignored, and are provided only for compatibility
    with the built-in json module.
    """
    parser = Parser()
    return parser.parse(s, True)


def parse_many(src, *, batch_size=1000000):
    """Parse NDJSON from memory, yielding independent Python values.

    See :ref:`streaming-records` for format and size limits.
    """
    return Parser().parse_many(src, batch_size=batch_size)


def load_many(source, *, batch_size=1000000):
    """Read NDJSON from a path or binary file using bounded input chunks.

    See :ref:`streaming-records` for format and size limits.
    """
    return Parser().load_many(source, batch_size=batch_size)


dumps = json.dumps
dump = json.dump
JSONEncoder = json.JSONEncoder
