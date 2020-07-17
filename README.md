![PyPI - License](https://img.shields.io/pypi/l/pysimdjson.svg?style=flat-square)
![Tests](https://github.com/TkTech/pysimdjson/workflows/Run%20tests/badge.svg)

# pysimdjson

Python bindings for the [simdjson][] project, a SIMD-accelerated JSON parser.

Bindings are currently tested on OS X, Linux, and Windows for Python 3.4+.

## Installation

If binary wheels are available for your platform, you can install from pip
with no further requirements:

    pip install pysimdjson

The project is self-contained, and has no additional dependencies. If binary
wheels are not available for your platform, or you want to build from source
for the best performance, you'll need a C++11-capable compiler to compile the
sources:

    pip install 'pysimdjson[dev]' --no-binary :all:

## Development and Testing

This project comes with a full test suite. To install development and testing
dependencies, use:

    pip install -e ".[dev]"

To also install 3rd party JSON libraries used for running benchmarks, use:

    pip install -e ".[benchmark]"

To run the tests, just type `pytest`. To also run the benchmarks, use `pytest
--runslow`.

To properly test on Windows, you need both a recent version of Visual Studio
(VS) as well as VS2015, patch 3. Older versions of CPython required portable
C/C++ extensions to be built with the same version of VS as the interpreter.
Use the [Developer Command Prompt][devprompt] to easily switch between
versions.

## How It Works

This project uses [pybind11][] to generate the low-level bindings on top of the
simdjson project. You can use it just like the built-in json module, or use
the simdjson-specific API for much better performance.

```python
import simdjson
doc = simdjson.loads('{"hello": "world"}')
```

## Making things faster

pysimdjson provides an api compatible with the built-in json module for
convenience, and this API is pretty fast (beating or tying all other Python
JSON libraries). However, it also provides a simdjson-specific API that can
perform significantly better.

### Don't load the entire document

95% of the time spent loading a JSON document into Python is spent in the
creation of Python objects, not the actual parsing of the document. You can
avoid all of this overhead by ignoring parts of the document you don't want.

pysimdjson supports this in two ways - the use of JSON pointers via `at()`,
or proxies for objects and lists.

```python
import simdjson
parser = simdjson.Parser()
doc = parser.parse(b'{"res": [{"name": "first"}, {"name": "second"}]')
```

For our sample above, we really just want the second entry in `res`, we
don't care about anything else. We can do this two ways:

```python
assert doc['res'][1]['name'] == 'second' # True
assert doc.at('res/1/name') == 'second' # True
```

Both of these approaches will be much faster than using `load/s()`, since
they avoid loading the parts of the document we didn't care about.

### Re-use the parser.

One of the easiest performance gains if you're working on many documents is
to re-use the parser.

```python
import simdjson
parser = simdjson.Parser()

for i in range(0, 100):
    doc = parser.parse(b'{"a": "b"})
```

This will drastically reduce the number of allocations being made, as it will
reuse the existing buffer when possible. If it's too small, it'll grow to fit.

## Performance Considerations

The actual parsing of a document is a small fraction (~5%) of the total time
spent bringing a JSON document into CPython. However, even in the case of
bringing the entire document into Python, pysimdjson will almost always be
faster or equivelent to other high-speed Python libraries.

There are two things to keep in mind when trying to get the best performance:

1. Do you really need the entire document? If you have a JSON document with
   thousands of keys but just need to check if the "published" key is
   `True`, use the JSON pointer interface to pull only a single field into
   Python.
2. There is significant overhead in calling a C++ function from Python.
   Minimizing the number of function calls can offer significant speedups in
   some use cases.

[simdjson]: https://github.com/lemire/simdjson
[pybind11]: https://pybind11.readthedocs.io/en/stable/
[devprompt]: https://docs.microsoft.com/en-us/dotnet/framework/tools/developer-command-prompt-for-vs
