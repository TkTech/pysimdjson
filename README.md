![PyPI - License](https://img.shields.io/pypi/l/pysimdjson.svg?style=flat-square)

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
simdjson project. This low-level interface is available at runtime in the
`csimdjson` module. Ex:

```python
import csimdjson

parser = csimdjson.parser()
doc = parser.parse('{"hello": "world"}')
```

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