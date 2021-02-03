![PyPI - License](https://img.shields.io/pypi/l/pysimdjson.svg?style=flat-square)
![Tests](https://github.com/TkTech/pysimdjson/workflows/Run%20tests/badge.svg)

# pysimdjson

Python bindings for the [simdjson][] project, a SIMD-accelerated JSON parser.
If SIMD instructions are unavailable a fallback parser is used, making
pysimdjson safe to use anywhere.

Bindings are currently tested on OS X, Linux, and Windows for Python version
3.5 to 3.9.

## 📝 Documentation

The latest documentation can be found at https://pysimdjson.tkte.ch.

If you've checked out the source code (for example to review a PR), you can
build the latest documentation by running `cd docs && make html`.

## 🎉 Installation

If binary wheels are available for your platform, you can install from pip
with no further requirements:

    pip install pysimdjson

Binary wheels are available for the following:

|                  | py3.5 | py3.6 | py3.7 | py3.8 | py3.9 | pypy3 |
| ---------------- | ----- | ----- | ----- | ----- | ----- | ----- |
| OS X (x86_64)    | y     | y     | y     | y     | y     | y     |
| Windows (x86_64) | x     | x     | y     | y     | y     | x     |
| Linux (x86_64)   | y     | y     | y     | y     | y     | x     |
| Linux (ARM64)    | y     | y     | y     | y     | y     | x     |


If binary wheels are not available for your platform, you'll need a
C++11-capable compiler to compile the sources:

    pip install pysimdjson --no-binary :all:

Both simdjson and pysimdjson support FreeBSD and Linux on ARM when built
from source.

## ⚗ Development and Testing

This project comes with a full test suite. To install development and testing
dependencies, use:

    pip install -e ".[test]"

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

pysimdjson supports this in two ways - the use of JSON pointers via
`at_pointer()`, or proxies for objects and lists.

```python
import simdjson
parser = simdjson.Parser()
doc = parser.parse(b'{"res": [{"name": "first"}, {"name": "second"}]}')
```

For our sample above, we really just want the second entry in `res`, we
don't care about anything else. We can do this two ways:

```python
assert doc['res'][1]['name'] == 'second' # True
assert doc.at_pointer('res/1/name') == 'second' # True
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
| Name                |   Min (μs) |   Max (μs) |   StdDev |      Ops |
|---------------------|------------|------------|----------|----------|
| ✨ simdjson-{canada} |   10.67130 |   22.89260 |  0.00465 | 60.30257 |
| yyjson-{canada}     |   11.29230 |   29.90640 |  0.00568 | 53.27890 |
| orjson-{canada}     |   11.90260 |   34.88260 |  0.00507 | 54.49605 |
| ujson-{canada}      |   18.17060 |   48.99410 |  0.00718 | 36.24892 |
| simplejson-{canada} |   39.24630 |   52.62860 |  0.00483 | 21.81617 |
| rapidjson-{canada}  |   41.04930 |   53.10800 |  0.00445 | 21.19078 |
| json-{canada}       |   44.68320 |   59.44410 |  0.00440 | 19.71509 |

### jsonexamples/canada.json deepest key
| Name                |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|---------------------|------------|------------|----------|-----------|
| ✨ simdjson-{canada} |    3.21360 |    6.88010 |  0.00044 | 285.83978 |
| yyjson-{canada}     |   10.62770 |   46.10050 |  0.01000 |  43.29310 |
| orjson-{canada}     |   12.54010 |   39.16080 |  0.00779 |  44.28928 |
| ujson-{canada}      |   17.93980 |   35.44960 |  0.00697 |  36.78481 |
| simplejson-{canada} |   38.58160 |   54.33290 |  0.00699 |  21.37382 |
| rapidjson-{canada}  |   40.69030 |   58.23460 |  0.00700 |  20.30349 |
| json-{canada}       |   43.88300 |   65.04480 |  0.00722 |  18.55929 |

### jsonexamples/twitter.json deserialization
| Name                 |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|----------------------|------------|------------|----------|-----------|
| orjson-{twitter}     |    2.36070 |   14.03050 |  0.00123 | 346.94307 |
| ✨ simdjson-{twitter} |    2.41350 |   12.01550 |  0.00117 | 359.49272 |
| yyjson-{twitter}     |    2.48130 |   12.03680 |  0.00112 | 353.03313 |
| ujson-{twitter}      |    2.62890 |   11.39370 |  0.00090 | 346.87994 |
| simplejson-{twitter} |    3.34600 |   11.08840 |  0.00098 | 270.58797 |
| json-{twitter}       |    3.35270 |   11.82610 |  0.00116 | 260.01943 |
| rapidjson-{twitter}  |    4.29320 |   13.81980 |  0.00128 | 197.91107 |

### jsonexamples/twitter.json deepest key
| Name                 |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|----------------------|------------|------------|----------|------------|
| ✨ simdjson-{twitter} |    0.33840 |    0.67200 |  0.00002 | 2800.32496 |
| orjson-{twitter}     |    2.38460 |   13.53120 |  0.00131 |  352.70788 |
| yyjson-{twitter}     |    2.48180 |   13.67470 |  0.00156 |  320.56731 |
| ujson-{twitter}      |    2.65230 |   11.65150 |  0.00125 |  331.69430 |
| json-{twitter}       |    3.34910 |   12.44890 |  0.00116 |  263.25854 |
| simplejson-{twitter} |    3.35760 |   15.61900 |  0.00137 |  262.36758 |
| rapidjson-{twitter}  |    4.31870 |   12.77490 |  0.00119 |  201.86510 |

### jsonexamples/github_events.json deserialization
| Name                       |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|----------------------------|------------|------------|----------|------------|
| orjson-{github_events}     |    0.18080 |    0.67020 |  0.00004 | 5041.29485 |
| ✨ simdjson-{github_events} |    0.19470 |    0.61450 |  0.00003 | 4725.63489 |
| yyjson-{github_events}     |    0.19710 |    0.53970 |  0.00004 | 4584.50870 |
| ujson-{github_events}      |    0.23760 |    1.33490 |  0.00004 | 3904.08715 |
| json-{github_events}       |    0.29030 |    1.32040 |  0.00009 | 3034.22530 |
| simplejson-{github_events} |    0.30210 |    0.82260 |  0.00005 | 3067.99997 |
| rapidjson-{github_events}  |    0.33010 |    0.92400 |  0.00005 | 2793.93274 |

### jsonexamples/github_events.json deepest key
| Name                       |   Min (μs) |   Max (μs) |   StdDev |         Ops |
|----------------------------|------------|------------|----------|-------------|
| ✨ simdjson-{github_events} |    0.03630 |    0.66110 |  0.00001 | 25259.19598 |
| orjson-{github_events}     |    0.18210 |    0.71230 |  0.00003 |  5073.48086 |
| yyjson-{github_events}     |    0.20030 |    0.61270 |  0.00003 |  4589.71299 |
| ujson-{github_events}      |    0.24260 |    1.05100 |  0.00007 |  3644.08240 |
| json-{github_events}       |    0.29310 |    2.38770 |  0.00011 |  2967.79019 |
| simplejson-{github_events} |    0.30580 |    1.39670 |  0.00007 |  2931.01646 |
| rapidjson-{github_events}  |    0.33340 |    0.80440 |  0.00004 |  2795.27887 |

### jsonexamples/citm_catalog.json deserialization
| Name                      |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|---------------------------|------------|------------|----------|-----------|
| orjson-{citm_catalog}     |    5.40140 |   17.76900 |  0.00314 | 130.33847 |
| yyjson-{citm_catalog}     |    5.77340 |   23.09490 |  0.00421 | 113.78942 |
| ✨ simdjson-{citm_catalog} |    6.00620 |   26.87570 |  0.00444 | 104.41073 |
| ujson-{citm_catalog}      |    6.34300 |   25.06400 |  0.00473 |  96.01414 |
| simplejson-{citm_catalog} |    9.54910 |   23.96350 |  0.00392 |  78.99315 |
| json-{citm_catalog}       |   10.21250 |   23.52610 |  0.00329 |  78.72180 |
| rapidjson-{citm_catalog}  |   10.81700 |   21.85400 |  0.00343 |  73.94939 |

### jsonexamples/citm_catalog.json deepest key
| Name                      |   Min (μs) |   Max (μs) |   StdDev |        Ops |
|---------------------------|------------|------------|----------|------------|
| ✨ simdjson-{citm_catalog} |    0.81040 |    2.11090 |  0.00015 | 1088.17698 |
| orjson-{citm_catalog}     |    5.37260 |   18.37890 |  0.00451 |  120.86345 |
| yyjson-{citm_catalog}     |    5.61430 |   23.18500 |  0.00548 |  110.29924 |
| ujson-{citm_catalog}      |    6.25850 |   30.79090 |  0.00604 |   95.50805 |
| simplejson-{citm_catalog} |    9.36560 |   24.44860 |  0.00510 |   77.50571 |
| json-{citm_catalog}       |   10.07650 |   25.29490 |  0.00450 |   76.18267 |
| rapidjson-{citm_catalog}  |   10.69120 |   27.84880 |  0.00493 |   70.98005 |

### jsonexamples/mesh.json deserialization
| Name              |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|-------------------|------------|------------|----------|-----------|
| yyjson-{mesh}     |    2.33710 |   13.01130 |  0.00171 | 331.50569 |
| ✨ simdjson-{mesh} |    2.52960 |   13.19230 |  0.00159 | 311.37935 |
| orjson-{mesh}     |    2.88770 |   12.13010 |  0.00152 | 287.31080 |
| ujson-{mesh}      |    3.64020 |   18.23620 |  0.00227 | 193.35645 |
| json-{mesh}       |    5.97130 |   13.58290 |  0.00136 | 150.01621 |
| rapidjson-{mesh}  |    7.54270 |   16.14480 |  0.00155 | 119.37806 |
| simplejson-{mesh} |    8.64370 |   16.35320 |  0.00136 | 106.25888 |

### jsonexamples/mesh.json deepest key
| Name              |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|-------------------|------------|------------|----------|-----------|
| ✨ simdjson-{mesh} |    1.02020 |    2.74930 |  0.00013 | 919.93044 |
| yyjson-{mesh}     |    2.30970 |   13.06730 |  0.00182 | 347.76076 |
| orjson-{mesh}     |    2.85260 |   12.41860 |  0.00156 | 290.19432 |
| ujson-{mesh}      |    3.59400 |   16.68610 |  0.00227 | 201.03704 |
| json-{mesh}       |    5.96300 |   19.18900 |  0.00185 | 146.04645 |
| rapidjson-{mesh}  |    7.43860 |   16.32260 |  0.00164 | 121.84979 |
| simplejson-{mesh} |    8.62160 |   21.89280 |  0.00221 | 101.30905 |

### jsonexamples/gsoc-2018.json deserialization
| Name                   |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|------------------------|------------|------------|----------|-----------|
| ✨ simdjson-{gsoc-2018} |    5.52590 |   16.27430 |  0.00178 | 145.59797 |
| yyjson-{gsoc-2018}     |    5.62040 |   16.46250 |  0.00168 | 155.97459 |
| orjson-{gsoc-2018}     |    5.78420 |   13.87300 |  0.00140 | 148.84293 |
| simplejson-{gsoc-2018} |    7.76200 |   15.26480 |  0.00142 | 114.98827 |
| ujson-{gsoc-2018}      |    7.96570 |   21.53840 |  0.00188 | 110.29162 |
| json-{gsoc-2018}       |    8.63300 |   19.26320 |  0.00172 | 102.78744 |
| rapidjson-{gsoc-2018}  |   10.55570 |   19.20210 |  0.00159 |  85.84087 |

### jsonexamples/gsoc-2018.json deepest key
| Name                   |   Min (μs) |   Max (μs) |   StdDev |       Ops |
|------------------------|------------|------------|----------|-----------|
| ✨ simdjson-{gsoc-2018} |    1.56020 |    4.20200 |  0.00024 | 570.15046 |
| yyjson-{gsoc-2018}     |    5.49930 |   14.89760 |  0.00158 | 161.14242 |
| orjson-{gsoc-2018}     |    5.72650 |   15.88270 |  0.00160 | 153.18169 |
| simplejson-{gsoc-2018} |    7.70780 |   18.78120 |  0.00169 | 116.90299 |
| ujson-{gsoc-2018}      |    7.91720 |   21.35300 |  0.00227 | 103.06755 |
| json-{gsoc-2018}       |    8.65190 |   19.99580 |  0.00188 | 103.86934 |
| rapidjson-{gsoc-2018}  |   10.52410 |   20.98870 |  0.00158 |  87.78973 |
<!-- BENCHMARK END -->


[simdjson]: https://github.com/lemire/simdjson
[pybind11]: https://pybind11.readthedocs.io/en/stable/
[devprompt]: https://docs.microsoft.com/en-us/dotnet/framework/tools/developer-command-prompt-for-vs
