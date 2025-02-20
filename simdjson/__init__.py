"""High-level bindings for the simdjson project."""
import json

try:
    from csimdjson import (
        Parser,
        Array,
        Object,
        MAXSIZE_BYTES,
        PADDING
    )
except ImportError:
    raise RuntimeError('Unable to import low-level simdjson bindings.')

_ALL_IMPORTS = [
    Parser,
    Array,
    Object,
    MAXSIZE_BYTES,
    PADDING
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


dumps = json.dumps
dump = json.dump
JSONEncoder = json.JSONEncoder
