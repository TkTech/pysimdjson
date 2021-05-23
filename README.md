![PyPI - License](https://img.shields.io/pypi/l/pysimdjson.svg?style=flat-square)
![Tests](https://github.com/TkTech/pysimdjson/workflows/Run%20tests/badge.svg)

# pysimdjson

Python bindings for the [simdjson][] project, a SIMD-accelerated JSON parser.
If SIMD instructions are unavailable a fallback parser is used, making
pysimdjson safe to use anywhere.

Bindings are currently tested on OS X, Linux, and Windows for Python version
3.6 to 3.9.

## 📝 Documentation

The latest documentation can be found at https://pysimdjson.tkte.ch.

If you've checked out the source code (for example to review a PR), you can
build the latest documentation by running `cd docs && make html`.

[simdjson]: https://github.com/lemire/simdjson
