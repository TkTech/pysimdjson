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
| ✨ simdjson-{canada} |   11.06660 |   32.72010 |  0.00572 | 50.49244 |
| orjson-{canada}      |   12.70790 |   26.67180 |  0.00424 | 55.58212 |
| simplejson-{canada}  |   38.48230 |   50.24570 |  0.00447 | 22.64854 |
| rapidjson-{canada}   |   39.67800 |   57.52180 |  0.00476 | 21.76358 |
| json-{canada}        |   42.54410 |   54.52020 |  0.00345 | 20.03848 |

### jsonexamples/canada.json deepest key
| Name                 |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|----------------------|------------|------------|----------|-----------|
| ✨ simdjson-{canada} |    3.38700 |   10.86230 |  0.00101 | 222.97853 |
| orjson-{canada}      |   13.34780 |   33.54840 |  0.00652 |  44.09761 |
| simplejson-{canada}  |   38.01830 |   69.71770 |  0.00843 |  20.47350 |
| rapidjson-{canada}   |   39.95230 |   59.47640 |  0.00667 |  20.16637 |
| json-{canada}        |   42.18320 |   63.19890 |  0.00686 |  19.37501 |

### jsonexamples/twitter.json deserialization
| Name                  |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|-----------------------|------------|------------|----------|-----------|
| orjson-{twitter}      |    2.25720 |    8.80010 |  0.00090 | 395.26644 |
| ✨ simdjson-{twitter} |    2.54290 |   17.11490 |  0.00189 | 250.52593 |
| simplejson-{twitter}  |    3.35020 |    9.28810 |  0.00094 | 272.00414 |
| rapidjson-{twitter}   |    4.39350 |   10.72390 |  0.00083 | 208.02216 |
| json-{twitter}        |    5.24810 |   11.10900 |  0.00086 | 177.25899 |

### jsonexamples/twitter.json deepest key
| Name                  |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|-----------------------|------------|------------|----------|------------|
| ✨ simdjson-{twitter} |    0.35660 |    3.52600 |  0.00020 | 2099.88860 |
| orjson-{twitter}      |    2.26630 |    9.70870 |  0.00104 |  384.04157 |
| simplejson-{twitter}  |    3.36320 |   11.10170 |  0.00120 |  263.55812 |
| rapidjson-{twitter}   |    4.40140 |   12.07110 |  0.00123 |  203.94305 |
| json-{twitter}        |    5.21540 |   15.52110 |  0.00112 |  178.51096 |

### jsonexamples/github_events.json deserialization
| Name                        |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|-----------------------------|------------|------------|----------|------------|
| orjson-{github_events}      |    0.17800 |    0.84640 |  0.00004 | 5232.35967 |
| ✨ simdjson-{github_events} |    0.20090 |    2.23790 |  0.00009 | 3685.60740 |
| json-{github_events}        |    0.28770 |    1.01060 |  0.00005 | 3247.96256 |
| simplejson-{github_events}  |    0.30560 |    1.19760 |  0.00003 | 3126.57352 |
| rapidjson-{github_events}   |    0.33170 |    0.67080 |  0.00003 | 2860.73395 |

### jsonexamples/github_events.json deepest key
| Name                        |   Min (μs) |   Max (μs) |   StdDev |         Ops |
|-----------------------------|------------|------------|----------|-------------|
| ✨ simdjson-{github_events} |    0.04050 |    0.33410 |  0.00001 | 21166.03658 |
| orjson-{github_events}      |    0.17970 |    0.53880 |  0.00002 |  5235.09246 |
| json-{github_events}        |    0.29140 |    0.98010 |  0.00004 |  3262.97633 |
| simplejson-{github_events}  |    0.30800 |    2.07340 |  0.00006 |  3087.47964 |
| rapidjson-{github_events}   |    0.33660 |    0.66480 |  0.00002 |  2799.91656 |

### jsonexamples/citm_catalog.json deserialization
| Name                       |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|----------------------------|------------|------------|----------|-----------|
| orjson-{citm_catalog}      |    5.42280 |   25.94490 |  0.00322 | 132.97562 |
| ✨ simdjson-{citm_catalog} |    6.24880 |   23.46540 |  0.00487 |  97.93701 |
| json-{citm_catalog}        |    9.20710 |   17.70010 |  0.00271 |  88.13338 |
| simplejson-{citm_catalog}  |    9.96980 |   20.16560 |  0.00314 |  81.37851 |
| rapidjson-{citm_catalog}   |   11.77450 |   41.98760 |  0.00442 |  70.71896 |

### jsonexamples/citm_catalog.json deepest key
| Name                       |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|----------------------------|------------|------------|----------|-----------|
| ✨ simdjson-{citm_catalog} |    0.87760 |    3.74490 |  0.00026 | 980.67148 |
| orjson-{citm_catalog}      |    5.42820 |   18.30850 |  0.00412 | 123.67493 |
| json-{citm_catalog}        |    9.08970 |   23.72150 |  0.00399 |  85.87864 |
| simplejson-{citm_catalog}  |    9.82740 |   24.80090 |  0.00447 |  79.48858 |
| rapidjson-{citm_catalog}   |   11.71590 |   28.64550 |  0.00490 |  67.48895 |

### jsonexamples/mesh.json deserialization
| Name               |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|--------------------|------------|------------|----------|-----------|
| ✨ simdjson-{mesh} |    2.61070 |   12.71490 |  0.00158 | 295.08199 |
| orjson-{mesh}      |    2.93950 |   11.48570 |  0.00127 | 292.54539 |
| json-{mesh}        |    5.60170 |   18.03550 |  0.00153 | 158.64945 |
| rapidjson-{mesh}   |    7.21990 |   21.84580 |  0.00201 | 123.34775 |
| simplejson-{mesh}  |    8.35430 |   16.78820 |  0.00182 | 106.41059 |

### jsonexamples/mesh.json deepest key
| Name               |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|--------------------|------------|------------|----------|-----------|
| ✨ simdjson-{mesh} |    1.01200 |    2.90980 |  0.00019 | 909.77466 |
| orjson-{mesh}      |    2.87630 |   10.38550 |  0.00133 | 299.85643 |
| json-{mesh}        |    5.61810 |   14.77090 |  0.00139 | 163.70380 |
| rapidjson-{mesh}   |    7.12080 |   19.14110 |  0.00210 | 119.10425 |
| simplejson-{mesh}  |    8.33190 |   24.92470 |  0.00315 |  96.34057 |


[simdjson]: https://github.com/lemire/simdjson
[pybind11]: https://pybind11.readthedocs.io/en/stable/
[devprompt]: https://docs.microsoft.com/en-us/dotnet/framework/tools/developer-command-prompt-for-vs
