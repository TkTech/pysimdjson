import json

try:
    from csimdjson import (
        # Objects
        Parser,
        Array,
        Object,
        # Enums
        error_code,
        # Constants
        MAXSIZE_BYTES,
        PADDING,
        DEFAULT_MAX_DEPTH
    )
except ImportError:
    raise RuntimeError('Unable to import low-level simdjson bindings.')

# Shuts up *all* linters complaining about our unused imports.
_ALL_IMPORTS = [
    Parser,
    Array,
    Object,
    error_code,
    MAXSIZE_BYTES,
    PADDING,
    DEFAULT_MAX_DEPTH
]


def load(fp, *, cls=None, object_hook=None, parse_float=None, parse_int=None,
         parse_constant=None, object_pairs_hook=None, **kwargs):
    """
    Same as the built-in json.load(), with the following exceptions:

        - All parse_* arguments are currently ignored. Allowing these would
          defeat most of the speed gains that come from using simdjson.
        - object_pairs_hook is ignored.
        - cls is ignored.
    """
    content = fp.read()
    if isinstance(content, str):
        content = content.encode('utf-8')

    parser = Parser()
    return parser.parse(content, True)


def loads(s, *, cls=None, object_hook=None, parse_float=None, parse_int=None,
          parse_constant=None, object_pairs_hook=None, **kwargs):
    """
    Same as the built-in json.loads(), with the following exceptions:

        - All parse_* arguments are currently ignored. Allowing these would
          defeat most of the speed gains that come from using simdjson.
        - object_pairs_hook is ignored.
        - cls is ignored.
    """
    if isinstance(s, str):
        s = s.encode('utf-8')

    parser = Parser()
    return parser.parse(s, True)


dumps = json.dumps
dump = json.dump
