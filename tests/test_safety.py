import gc
import pytest


def test_parser_reuse(parser):
    """
    In the simdjson DOM model, if the parser is re-used, existing Object and
    Array wrappers may point either into freed memory, random memory, or the
    new document. pysimdjson should prevent this.
    """
    p = parser.parse(b'{"deep": {"object": "lifecycle"}}')
    # Not a typo, keep this, we're keeping the object alive for the next call
    # to parse().
    p

    # Assuming our safety checks are working, this will see that an object (p)
    # still exists that references the parser document and will refuse to
    # parse.
    with pytest.raises(RuntimeError):
        parser.parse(b'{"deep": {"lifecycle": "object"}}')

    # Explicitly delete the existing object pointing into the parser.
    del p
    # ... and force a garbage collection for PyPy.
    gc.collect()

    # ... and try re-using the parser again.
    parser.parse(b'{"deep": {"lifecycle": "object"}}')
