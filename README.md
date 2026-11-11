![PyPI - License](https://img.shields.io/pypi/l/pysimdjson.svg?style=flat-square)
[![Tests](https://github.com/TkTech/pysimdjson/actions/workflows/release.yml/badge.svg)](https://github.com/TkTech/pysimdjson/actions/workflows/release.yml)

# pysimdjson

Python bindings for the [simdjson][] project, a SIMD-accelerated JSON parser.
If SIMD instructions are unavailable a fallback parser is used, making
pysimdjson safe to use anywhere.

Bindings are currently tested on OS X, Linux, and Windows for Python version
3.11 to 3.15.

## 📝 Documentation

The latest documentation can be found at https://pysimdjson.tkte.ch.

If you've checked out the source code (for example to review a PR), you can
build the latest documentation by running `uv run --group dev make -C docs html`.

## 📈 Benchmarks

pysimdjson compares well against most libraries. The full benchmarks can be
found in its sister project [json_benchmark][].

[simdjson]: https://github.com/lemire/simdjson
[json_benchmark]: https://github.com/tktech/json_benchmark

## Building locally

Building from source requires Python 3.11+ and a C++11-compatible compiler.
On Windows, install Visual Studio C++ build tools for your target architecture.

Install uv with `python -m pip install uv`, then from your checkout run:

```bash
uv sync --group dev
uv run --group dev --reinstall-package pysimdjson pytest
```

Python changes are visible immediately in this editable installation. After
changing Cython or C++ sources, rebuild the extension with
`uv sync --group dev --reinstall-package pysimdjson`.
