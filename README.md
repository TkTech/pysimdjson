![PyPI - License](https://img.shields.io/pypi/l/pysimdjson.svg?style=flat-square)
![Tests](https://github.com/TkTech/pysimdjson/workflows/Run%20tests/badge.svg)

# pysimdjson

Python bindings for the [simdjson][] project, a SIMD-accelerated JSON parser.
If SIMD instructions are unavailable a fallback parser is used, making
pysimdjson safe to use anywhere.

Bindings are currently tested on OS X, Linux, and Windows for Python version
3.5 to 3.9.

## 🎉 Installation

If binary wheels are available for your platform, you can install from pip
with no further requirements:

    pip install pysimdjson

Binary wheels are available for x86_64 on the following:

|          | py3.5 | py3.6 | py3.7 | py3.8 | pypy3 |
| -------- | ----- | ----- | ----- | ----- | ----- |
| OS X     | y     | y     | y     | y     | y     |
| Windows  | x     | x     | y     | y     | x     |
| Linux    | y     | y     | y     | y     | x     |


If binary wheels are not available for your platform, you'll need a
C++11-capable compiler to compile the sources:

    pip install 'pysimdjson[dev]' --no-binary :all:

Both simddjson and pysimdjson support FreeBSD and Linux on ARM when built
from source.

## ⚗ Development and Testing

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

## 🚀 Making things faster

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

## 📈 Benchmarks

pysimdjson compares well against most libraries for the default `load/loads()`,
which creates full python objects immediately.

pysimdjson performs *significantly* better when only part of the document is of
interest. For each test file we show the time taken to completely deserialize
the document into Python objects, as well as the time to get the deepest key in
each file. The second approach avoids all unnecessary object creation.

### jsonexamples/canada.json deserialization
| Name                 |   Min (μs) |   Max (μs) |   StdDev |      Ops |
|----------------------|------------|------------|----------|----------|
| ✨ simdjson-{canada} |    0.01049 |    0.02536 |  0.00451 | 59.44683 |
| orjson-{canada}      |    0.01247 |    0.03111 |  0.00471 | 52.82846 |
| simplejson-{canada}  |    0.03851 |    0.05708 |  0.00525 | 21.94591 |
| rapidjson-{canada}   |    0.03961 |    0.05879 |  0.00529 | 20.79124 |
| json-{canada}        |    0.04341 |    0.05538 |  0.00402 | 19.95942 |

### jsonexamples/canada.json deepest key
| Name                 |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|----------------------|------------|------------|----------|-----------|
| ✨ simdjson-{canada} |    0.00321 |    0.00765 |  0.00068 | 279.84267 |
| orjson-{canada}      |    0.01276 |    0.04388 |  0.00821 |  41.92871 |
| simplejson-{canada}  |    0.04013 |    0.06736 |  0.00859 |  19.08933 |
| rapidjson-{canada}   |    0.04050 |    0.06654 |  0.00754 |  18.96156 |
| json-{canada}        |    0.04246 |    0.05979 |  0.00606 |  19.39106 |

### jsonexamples/twitter.json deserialization
| Name                  |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|-----------------------|------------|------------|----------|-----------|
| orjson-{twitter}      |    0.00222 |    0.00968 |  0.00094 | 387.14526 |
| ✨ simdjson-{twitter} |    0.00247 |    0.01043 |  0.00108 | 331.42196 |
| json-{twitter}        |    0.00326 |    0.01236 |  0.00107 | 273.34453 |
| simplejson-{twitter}  |    0.00360 |    0.01080 |  0.00118 | 233.11392 |
| rapidjson-{twitter}   |    0.00435 |    0.01319 |  0.00118 | 200.19221 |

### jsonexamples/twitter.json deepest key
| Name                  |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|-----------------------|------------|------------|----------|------------|
| ✨ simdjson-{twitter} |    0.00035 |    0.00105 |  0.00007 | 2613.89432 |
| orjson-{twitter}      |    0.00222 |    0.01230 |  0.00110 |  394.58464 |
| json-{twitter}        |    0.00326 |    0.01025 |  0.00123 |  257.92422 |
| simplejson-{twitter}  |    0.00360 |    0.01383 |  0.00136 |  239.89460 |
| rapidjson-{twitter}   |    0.00436 |    0.01243 |  0.00119 |  201.08697 |

### jsonexamples/github_events.json deserialization
| Name                        |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|-----------------------------|------------|------------|----------|------------|
| orjson-{github_events}      |    0.00018 |    0.00052 |  0.00002 | 5385.78812 |
| ✨ simdjson-{github_events} |    0.00020 |    0.00052 |  0.00002 | 4670.27409 |
| json-{github_events}        |    0.00028 |    0.00092 |  0.00005 | 3267.96841 |
| simplejson-{github_events}  |    0.00033 |    0.00112 |  0.00008 | 2663.16211 |
| rapidjson-{github_events}   |    0.00033 |    0.00091 |  0.00004 | 2745.68280 |

### jsonexamples/github_events.json deepest key
| Name                        |   Min (μs) |   Max (μs) |   StdDev |         Ops |
|-----------------------------|------------|------------|----------|-------------|
| ✨ simdjson-{github_events} |    0.00004 |    0.00047 |  0.00001 | 24332.04800 |
| orjson-{github_events}      |    0.00018 |    0.00092 |  0.00004 |  5252.38777 |
| json-{github_events}        |    0.00029 |    0.00085 |  0.00005 |  3246.92854 |
| rapidjson-{github_events}   |    0.00033 |    0.00097 |  0.00005 |  2769.23916 |
| simplejson-{github_events}  |    0.00034 |    0.00113 |  0.00007 |  2716.07533 |

### jsonexamples/citm_catalog.json deserialization
| Name                       |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|----------------------------|------------|------------|----------|-----------|
| orjson-{citm_catalog}      |    0.00524 |    0.01677 |  0.00308 | 128.53221 |
| ✨ simdjson-{citm_catalog} |    0.00599 |    0.02122 |  0.00367 | 116.89787 |
| json-{citm_catalog}        |    0.01239 |    0.02367 |  0.00297 |  67.50124 |
| simplejson-{citm_catalog}  |    0.01512 |    0.03227 |  0.00474 |  50.53492 |
| rapidjson-{citm_catalog}   |    0.01873 |    0.03465 |  0.00373 |  46.83095 |

### jsonexamples/citm_catalog.json deepest key
| Name                       |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|----------------------------|------------|------------|----------|------------|
| ✨ simdjson-{citm_catalog} |    0.00087 |    0.00212 |  0.00015 | 1028.03869 |
| orjson-{citm_catalog}      |    0.00523 |    0.02518 |  0.00486 |  107.92591 |
| json-{citm_catalog}        |    0.01211 |    0.02485 |  0.00401 |   66.42090 |
| simplejson-{citm_catalog}  |    0.01471 |    0.03422 |  0.00532 |   52.54649 |
| rapidjson-{citm_catalog}   |    0.01833 |    0.03874 |  0.00513 |   45.29510 |

### jsonexamples/mesh.json deserialization
| Name               |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|--------------------|------------|------------|----------|-----------|
| ✨ simdjson-{mesh} |    0.00250 |    0.01111 |  0.00147 | 315.56540 |
| orjson-{mesh}      |    0.00289 |    0.01416 |  0.00172 | 246.36728 |
| json-{mesh}        |    0.00562 |    0.01712 |  0.00182 | 144.62005 |
| rapidjson-{mesh}   |    0.00714 |    0.01548 |  0.00178 | 119.87250 |
| simplejson-{mesh}  |    0.00833 |    0.01829 |  0.00156 | 107.92900 |

### jsonexamples/mesh.json deepest key
| Name               |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|--------------------|------------|------------|----------|------------|
| ✨ simdjson-{mesh} |    0.00092 |    0.00210 |  0.00008 | 1041.88051 |
| orjson-{mesh}      |    0.00283 |    0.01160 |  0.00151 |  286.51844 |
| json-{mesh}        |    0.00562 |    0.01375 |  0.00148 |  149.79532 |
| rapidjson-{mesh}   |    0.00708 |    0.01900 |  0.00201 |  119.81628 |
| simplejson-{mesh}  |    0.00826 |    0.01742 |  0.00178 |  107.73594 |


[simdjson]: https://github.com/lemire/simdjson
[pybind11]: https://pybind11.readthedocs.io/en/stable/
[devprompt]: https://docs.microsoft.com/en-us/dotnet/framework/tools/developer-command-prompt-for-vs
