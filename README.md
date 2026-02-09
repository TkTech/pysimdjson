![PyPI - License](https://img.shields.io/pypi/l/pysimdjson.svg?style=flat-square)
[![tests](https://github.com/TkTech/pysimdjson/actions/workflows/release.yml/badge.svg)](https://github.com/TkTech/pysimdjson/actions/workflows/release.yml)

# pysimdjson

Python bindings for the [simdjson][] project, a SIMD-accelerated JSON parser.
If SIMD instructions are unavailable a fallback parser is used, making
pysimdjson safe to use anywhere.

Bindings are currently tested on OS X, Linux, and Windows for Python version
3.9 to 3.12.


## 📈 Documentation

The latest documentation can be found at https://pysimdjson.tkte.ch.

If you've checked out the source code (for example to review a PR), you can
build the latest documentation by running `cd docs && make html`.

## 📈 Benchmarks

pysimdjson compares well against most libraries. The full benchmarks can be
found in its sister project [json_benchmark][].

[simdjson]: https://github.com/lemire/simdjson
[json_benchmark]: https://github.com/tktech/json_benchmark

## 📈 Building Locally

To build pysimdjson from source, you'll need Python 3.9+ and a C++ compiler.

1. **Install uv** (if not already installed):
   ```bash
   pip install uv
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/TkTech/pysimdjson.git
   cd pysimdjson
   ```

3. **Build the package**:
   ```bash
   uv sync
   ```

4. **(Optional) Run tests**:
   ```bash
   uv run pytest
   ```

5. **(Optional) Build documentation**:
   ```bash
   cd docs && uv run make html
   ```
