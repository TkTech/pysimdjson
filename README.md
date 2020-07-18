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

    ----------------------- benchmark 'canada.json deserialization': 5 tests -----------------------
    Name (time in ms)                       Min                Max            StdDev                OPS
    -------------------------------------------------------------------------------------------------------------
    test_loads[simdjson-{canada}]       10.4811 (1.0)      24.3397 (1.0)      4.7388 (1.39)     58.9446 (1.0)
    test_loads[orjson-{canada}]         11.9215 (1.14)     26.6154 (1.09)     4.5960 (1.35)     56.4259 (0.96)
    test_loads[rapidjson-{canada}]      39.5539 (3.77)     55.2940 (2.27)     4.5611 (1.34)     21.9320 (0.37)
    test_loads[simplejson-{canada}]     40.1241 (3.83)     80.6007 (3.31)     9.9864 (2.93)     16.6949 (0.28)
    test_loads[json-{canada}]           44.1405 (4.21)     54.2507 (2.23)     3.4104 (1.0)      20.0804 (0.34)
    -------------------------------------------------------------------------------------------------------------

    ----------------------- benchmark 'citm_catalog.json deserialization': 5 tests ------------------------
    Name (time in ms)                             Min                Max            StdDev                 OPS
    --------------------------------------------------------------------------------------------------------------------
    test_loads[orjson-{citm_catalog}]          5.2760 (1.0)      20.9524 (1.13)     3.4629 (1.20)     121.1383 (1.0)
    test_loads[simdjson-{citm_catalog}]        6.5239 (1.24)     25.6092 (1.38)     4.8020 (1.67)      94.2306 (0.78)
    test_loads[json-{citm_catalog}]            8.9343 (1.69)     18.5411 (1.0)      2.8824 (1.0)       90.8202 (0.75)
    test_loads[simplejson-{citm_catalog}]     14.5374 (2.76)     32.7292 (1.77)     4.5192 (1.57)      48.5961 (0.40)
    test_loads[rapidjson-{citm_catalog}]      19.2895 (3.66)     40.0359 (2.16)     5.4149 (1.88)      41.0418 (0.34)
    --------------------------------------------------------------------------------------------------------------------

    ----------------------------- benchmark 'github_events.json deserialization': 5 tests ----------------------------
    Name (time in us)                               Min                   Max              StdDev            OPS (Kops/s)
    -------------------------------------------------------------------------------------------------------------------------------
    test_loads[orjson-{github_events}]         172.2000 (1.0)        739.8999 (1.0)       47.4074 (1.16)           5.2325 (1.0)
    test_loads[simdjson-{github_events}]       202.8000 (1.18)     4,079.4000 (5.51)     186.2712 (4.55)           2.8892 (0.55)
    test_loads[json-{github_events}]           287.1001 (1.67)       957.9001 (1.29)      40.9069 (1.0)            3.2871 (0.63)
    test_loads[simplejson-{github_events}]     309.3000 (1.80)     5,297.9999 (7.16)     255.8534 (6.25)           1.6543 (0.32)
    test_loads[rapidjson-{github_events}]      332.7000 (1.93)     1,691.7000 (2.29)     109.8334 (2.68)           2.3902 (0.46)
    -------------------------------------------------------------------------------------------------------------------------------

    ----------------------- benchmark 'mesh.json deserialization': 5 tests -----------------------
    Name (time in ms)                    Min                Max            StdDev                 OPS
    -----------------------------------------------------------------------------------------------------------
    test_loads[simdjson-{mesh}]       2.6469 (1.0)      16.6805 (1.33)     1.9141 (1.15)     268.1294 (1.0)
    test_loads[orjson-{mesh}]         2.8860 (1.09)     12.4975 (1.0)      1.6662 (1.0)      235.8765 (0.88)
    test_loads[json-{mesh}]           5.6511 (2.13)     14.4534 (1.16)     1.7656 (1.06)     139.7706 (0.52)
    test_loads[rapidjson-{mesh}]      7.1840 (2.71)     15.6312 (1.25)     1.7456 (1.05)     118.8410 (0.44)
    test_loads[simplejson-{mesh}]     8.8135 (3.33)     19.1758 (1.53)     2.6535 (1.59)      86.7714 (0.32)
    -----------------------------------------------------------------------------------------------------------

    ----------------------- benchmark 'twitter.json deserialization': 5 tests -----------------------
    Name (time in ms)                       Min                Max            StdDev                 OPS
    --------------------------------------------------------------------------------------------------------------
    test_loads[orjson-{twitter}]         2.2691 (1.0)      15.3392 (1.14)     1.4043 (1.53)     341.2678 (1.0)
    test_loads[simdjson-{twitter}]       2.8037 (1.24)     32.3851 (2.41)     3.8123 (4.15)     156.0232 (0.46)
    test_loads[simplejson-{twitter}]     3.5374 (1.56)     23.4863 (1.75)     2.7789 (3.03)     146.4329 (0.43)
    test_loads[rapidjson-{twitter}]      4.4712 (1.97)     29.4311 (2.19)     2.6441 (2.88)     145.9760 (0.43)
    test_loads[json-{twitter}]           5.2692 (2.32)     13.4483 (1.0)      0.9182 (1.0)      175.3306 (0.51)
    --------------------------------------------------------------------------------------------------------------

pysimdjson performs *significantly* better when only part of the document is of
interest. The below benchmarks find the deepest key in each test document and
time how long it takes to retrieve.

    benchmark "canada.json deepest key (['features', 0, 'geometry', 'coordinates', 479, 5275, 1])": 5 tests
    Name (time in ms)                             Min                Max             StdDev                 OPS
    ---------------------------------------------------------------------------------------------------------------------
    test_deepest_key[simdjson-{canada}]        3.2434 (1.0)      14.0368 (1.0)       2.1028 (1.0)      166.5185 (1.0)
    test_deepest_key[orjson-{canada}]         13.1776 (4.06)     41.3261 (2.94)      7.9412 (3.78)      40.7021 (0.24)
    test_deepest_key[json-{canada}]           42.3800 (13.07)    64.9336 (4.63)      7.4610 (3.55)      19.1264 (0.11)
    test_deepest_key[rapidjson-{canada}]      45.2168 (13.94)    79.9457 (5.70)      9.6121 (4.57)      17.8654 (0.11)
    test_deepest_key[simplejson-{canada}]     49.5191 (15.27)    99.9450 (7.12)     16.6635 (7.92)      14.0854 (0.08)
    ---------------------------------------------------------------------------------------------------------------------

    benchmark "citm_catalog.json deepest key (['performances', 242, 'seatCategories', 4, 'areas', 5, 'blockIds'])": 5 tests
    Name (time in us)                                       Min                    Max                StdDev                 OPS
    --------------------------------------------------------------------------------------------------------------------------------------
    test_deepest_key[simdjson-{citm_catalog}]          916.3000 (1.0)       3,963.8000 (1.0)        454.2639 (1.0)      694.5146 (1.0)
    test_deepest_key[orjson-{citm_catalog}]          5,289.0000 (5.77)     24,022.8999 (6.06)     5,030.3328 (11.07)    107.4222 (0.15)
    test_deepest_key[json-{citm_catalog}]            8,959.6000 (9.78)     20,410.5000 (5.15)     3,981.1498 (8.76)      84.6871 (0.12)
    test_deepest_key[simplejson-{citm_catalog}]     14,594.5000 (15.93)    43,028.8000 (10.86)    7,555.8160 (16.63)     44.3869 (0.06)
    test_deepest_key[rapidjson-{citm_catalog}]      18,541.0000 (20.23)    37,101.6000 (9.36)     5,521.5665 (12.15)     42.3854 (0.06)
    --------------------------------------------------------------------------------------------------------------------------------------

    --------- benchmark "github_events.json deepest key ([27, 'payload', 'commits', 0, 'author', 'name'])": 5 tests --------
    Name (time in us)                                     Min                   Max              StdDev            OPS (Kops/s)
    -------------------------------------------------------------------------------------------------------------------------------------
    test_deepest_key[simdjson-{github_events}]        39.8000 (1.0)        341.7000 (1.0)       17.7718 (1.0)           19.2912 (1.0)
    test_deepest_key[orjson-{github_events}]         172.5999 (4.34)       608.7000 (1.78)      46.4721 (2.61)           5.2461 (0.27)
    test_deepest_key[json-{github_events}]           288.9000 (7.26)     1,243.4999 (3.64)      50.7749 (2.86)           3.2650 (0.17)
    test_deepest_key[simplejson-{github_events}]     310.6000 (7.80)     2,786.4000 (8.15)     224.7922 (12.65)          1.9316 (0.10)
    test_deepest_key[rapidjson-{github_events}]      335.4001 (8.43)     1,401.4000 (4.10)      94.5639 (5.32)           2.4839 (0.13)
    -------------------------------------------------------------------------------------------------------------------------------------

    ------------------ benchmark "mesh.json deepest key (['batches', 0, 'usedBones', 0])": 5 tests -----------------
    Name (time in us)                              Min                    Max                StdDev                 OPS
    -----------------------------------------------------------------------------------------------------------------------------
    test_deepest_key[simdjson-{mesh}]         936.4000 (1.0)       3,916.1000 (1.0)        332.4972 (1.0)      829.6598 (1.0)
    test_deepest_key[orjson-{mesh}]         2,849.8999 (3.04)     11,593.0000 (2.96)     1,486.7968 (4.47)     289.6456 (0.35)
    test_deepest_key[json-{mesh}]           5,649.7001 (6.03)     18,443.2999 (4.71)     2,301.1871 (6.92)     145.8578 (0.18)
    test_deepest_key[rapidjson-{mesh}]      7,162.4001 (7.65)     15,666.7000 (4.00)     1,947.8277 (5.86)     115.8153 (0.14)
    test_deepest_key[simplejson-{mesh}]     8,340.0999 (8.91)     17,453.5000 (4.46)     2,157.5231 (6.49)      99.9991 (0.12)
    -----------------------------------------------------------------------------------------------------------------------------

    benchmark "twitter.json deepest key (['statuses', 97, 'retweeted_status', 'user', 'entities', 'url', 'urls', 0, 'indices', 1])": 5 tests
    Name (time in us)                                 Min                    Max                StdDev                   OPS
    ----------------------------------------------------------------------------------------------------------------------------------
    test_deepest_key[simdjson-{twitter}]         359.6001 (1.0)       7,383.8000 (1.0)        323.3750 (1.0)      1,384.0209 (1.0)
    test_deepest_key[orjson-{twitter}]         2,258.2000 (6.28)     20,239.7000 (2.74)     1,664.2791 (5.15)       314.2592 (0.23)
    test_deepest_key[simplejson-{twitter}]     3,589.0000 (9.98)     27,081.9000 (3.67)     3,532.4124 (10.92)      114.6335 (0.08)
    test_deepest_key[rapidjson-{twitter}]      4,442.3001 (12.35)    17,075.6001 (2.31)     1,834.4635 (5.67)       170.7921 (0.12)
    test_deepest_key[json-{twitter}]           5,256.4000 (14.62)    11,935.7000 (1.62)     1,070.5530 (3.31)       174.2813 (0.13)
    ----------------------------------------------------------------------------------------------------------------------------------

[simdjson]: https://github.com/lemire/simdjson
[pybind11]: https://pybind11.readthedocs.io/en/stable/
[devprompt]: https://docs.microsoft.com/en-us/dotnet/framework/tools/developer-command-prompt-for-vs
