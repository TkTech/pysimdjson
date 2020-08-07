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

Binary wheels are available for the following:

|                  | py3.5 | py3.6 | py3.7 | py3.8 | pypy3 |
| ---------------- | ----- | ----- | ----- | ----- | ----- |
| OS X (x86_64)    | y     | y     | y     | y     | y     |
| Windows (x86_64) | x     | x     | y     | y     | x     |
| Linux (x86_64)   | y     | y     | y     | y     | x     |
| Linux (ARM64)    | y     | y     | y     | y     | x     |


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
doc = parser.parse(b'{"res": [{"name": "first"}, {"name": "second"}]}')
```

For our sample above, we really just want the second entry in `res`, we
don't care about anything else. We can do this two ways:

```python
assert doc['res'][1]['name'] == 'second' # True
assert doc.at('res/1/name') == 'second' # True
```

Both of these approaches will be much faster than using `load/s()`, since
they avoid loading the parts of the document we didn't care about.

Both `Object` and `Array` have a `mini` property that returns their entire
content as a minified Python `str`. A message router for example would only
parse the document and retrieve a single property, the destination, and forward
the payload without ever turning it into a Python object. Here's a (bad)
example:

```python
import simdjson

@app.route('/store', methods=['POST'])
def store():
    parser = simdjson.Parser()
    doc = parser.parse(request.data)
    redis.set(doc['key'], doc.mini)
```

With this, doc could contain thousands of objects, but the only one loaded
into a python object was `key`, and we even minified the content as we went.

### Re-use the parser.

One of the easiest performance gains if you're working on many documents is
to re-use the parser.

```python
import simdjson
parser = simdjson.Parser()

for i in range(0, 100):
    doc = parser.parse(b'{"a": "b"}')
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

<!-- BENCHMARK START -->

### jsonexamples/canada.json deserialization
| Name                 |   Min (μs) |   Max (μs) |   StdDev |      Ops |
|----------------------|------------|------------|----------|----------|
| ✨ simdjson-{canada} |   10.61630 |   27.12380 |  0.00442 | 58.42790 |
| orjson-{canada}      |   11.97230 |   29.95960 |  0.00469 | 56.21902 |
| ujson-{canada}       |   19.12120 |   60.73670 |  0.01320 | 26.66618 |
| simplejson-{canada}  |   39.64180 |   59.80270 |  0.00535 | 20.51313 |
| rapidjson-{canada}   |   40.57460 |   78.20690 |  0.01444 | 17.10311 |
| json-{canada}        |   42.95370 |   62.18130 |  0.00470 | 20.21549 |

### jsonexamples/canada.json deepest key
| Name                 |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|----------------------|------------|------------|----------|-----------|
| ✨ simdjson-{canada} |    3.38440 |    7.60380 |  0.00071 | 255.69203 |
| ujson-{canada}       |   11.10420 |   34.35320 |  0.00742 |  49.72907 |
| orjson-{canada}      |   12.92510 |   45.33800 |  0.00745 |  41.44936 |
| simplejson-{canada}  |   38.92410 |   64.06250 |  0.00856 |  19.70330 |
| rapidjson-{canada}   |   41.22570 |   66.68340 |  0.00756 |  19.22791 |
| json-{canada}        |   43.08250 |   64.75990 |  0.00661 |  18.15876 |

### jsonexamples/twitter.json deserialization
| Name                  |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|-----------------------|------------|------------|----------|-----------|
| orjson-{twitter}      |    2.29380 |    8.67020 |  0.00094 | 372.10773 |
| ✨ simdjson-{twitter} |    2.49010 |   22.30540 |  0.00198 | 281.95565 |
| ujson-{twitter}       |    2.74350 |   12.06470 |  0.00105 | 317.20009 |
| simplejson-{twitter}  |    3.35320 |   19.56840 |  0.00202 | 217.32882 |
| rapidjson-{twitter}   |    4.32850 |   13.21370 |  0.00119 | 194.83892 |
| json-{twitter}        |    5.27190 |   11.25140 |  0.00117 | 167.84380 |

### jsonexamples/twitter.json deepest key
| Name                  |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|-----------------------|------------|------------|----------|------------|
| ✨ simdjson-{twitter} |    0.35740 |    2.01060 |  0.00009 | 2423.86485 |
| orjson-{twitter}      |    2.29750 |   11.01000 |  0.00105 |  366.48762 |
| ujson-{twitter}       |    2.76260 |   14.13210 |  0.00143 |  285.69895 |
| simplejson-{twitter}  |    3.35340 |   13.34750 |  0.00118 |  257.05624 |
| rapidjson-{twitter}   |    4.31330 |   12.43220 |  0.00141 |  192.75979 |
| json-{twitter}        |    5.23560 |   13.85480 |  0.00126 |  168.04882 |

### jsonexamples/github_events.json deserialization
| Name                        |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|-----------------------------|------------|------------|----------|------------|
| orjson-{github_events}      |    0.17850 |    0.62230 |  0.00002 | 5331.74983 |
| ✨ simdjson-{github_events} |    0.19760 |    2.36700 |  0.00009 | 3905.95971 |
| ujson-{github_events}       |    0.25860 |    0.67530 |  0.00003 | 3642.89767 |
| json-{github_events}        |    0.28910 |    1.09600 |  0.00009 | 2924.08415 |
| simplejson-{github_events}  |    0.30620 |    1.29520 |  0.00005 | 3007.32539 |
| rapidjson-{github_events}   |    0.33290 |    1.15310 |  0.00006 | 2654.55940 |

### jsonexamples/github_events.json deepest key
| Name                        |   Min (μs) |   Max (μs) |   StdDev |         Ops |
|-----------------------------|------------|------------|----------|-------------|
| ✨ simdjson-{github_events} |    0.03950 |    3.31210 |  0.00005 | 15973.82108 |
| orjson-{github_events}      |    0.18030 |    0.65220 |  0.00005 |  4911.43253 |
| ujson-{github_events}       |    0.26070 |    0.96760 |  0.00005 |  3549.92113 |
| json-{github_events}        |    0.29040 |    1.54090 |  0.00007 |  3047.37921 |
| simplejson-{github_events}  |    0.30920 |    0.98670 |  0.00008 |  2953.84031 |
| rapidjson-{github_events}   |    0.33390 |    1.56730 |  0.00010 |  2461.45389 |

### jsonexamples/citm_catalog.json deserialization
| Name                       |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|----------------------------|------------|------------|----------|-----------|
| orjson-{citm_catalog}      |    5.24950 |   18.22640 |  0.00323 | 129.49044 |
| ✨ simdjson-{citm_catalog} |    6.05650 |   29.15550 |  0.00584 |  70.17580 |
| ujson-{citm_catalog}       |    6.24130 |   18.69410 |  0.00373 | 109.60956 |
| json-{citm_catalog}        |    9.10930 |   26.54630 |  0.00414 |  76.55235 |
| simplejson-{citm_catalog}  |   13.69630 |   28.63450 |  0.00401 |  57.28718 |
| rapidjson-{citm_catalog}   |   21.78300 |   65.30240 |  0.01055 |  28.63350 |

### jsonexamples/citm_catalog.json deepest key
| Name                       |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|----------------------------|------------|------------|----------|------------|
| ✨ simdjson-{citm_catalog} |    0.87070 |    2.86480 |  0.00019 | 1056.22226 |
| orjson-{citm_catalog}      |    5.40520 |   26.24650 |  0.00551 |  102.43563 |
| ujson-{citm_catalog}       |    6.38280 |   26.49210 |  0.00562 |   96.65066 |
| json-{citm_catalog}        |    9.16770 |   29.45910 |  0.00498 |   76.90314 |
| simplejson-{citm_catalog}  |   13.66750 |   30.54480 |  0.00471 |   57.54416 |
| rapidjson-{citm_catalog}   |   19.16620 |   49.23040 |  0.00714 |   36.04769 |

### jsonexamples/mesh.json deserialization
| Name               |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|--------------------|------------|------------|----------|-----------|
| ✨ simdjson-{mesh} |    2.60850 |   17.85500 |  0.00189 | 276.39681 |
| ujson-{mesh}       |    2.80000 |   11.36520 |  0.00148 | 297.40696 |
| orjson-{mesh}      |    2.87780 |   14.34770 |  0.00156 | 272.06333 |
| json-{mesh}        |    5.69520 |   22.03140 |  0.00282 | 132.44125 |
| rapidjson-{mesh}   |    7.28240 |   24.61470 |  0.00249 | 113.59051 |
| simplejson-{mesh}  |    8.37720 |   18.80480 |  0.00201 | 104.81092 |

### jsonexamples/mesh.json deepest key
| Name               |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|--------------------|------------|------------|----------|-----------|
| ✨ simdjson-{mesh} |    1.01600 |   12.12980 |  0.00067 | 619.16472 |
| ujson-{mesh}       |    2.75500 |   14.19920 |  0.00166 | 309.06497 |
| orjson-{mesh}      |    2.84420 |   24.41680 |  0.00248 | 245.50994 |
| json-{mesh}        |    5.63860 |   14.53620 |  0.00160 | 154.31889 |
| rapidjson-{mesh}   |    7.11940 |   18.68600 |  0.00208 | 117.20282 |
| simplejson-{mesh}  |    8.27930 |   19.76000 |  0.00207 | 106.66946 |
<!-- BENCHMARK END -->


[simdjson]: https://github.com/lemire/simdjson
[pybind11]: https://pybind11.readthedocs.io/en/stable/
[devprompt]: https://docs.microsoft.com/en-us/dotnet/framework/tools/developer-command-prompt-for-vs

