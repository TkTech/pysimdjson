![PyPI - License](https://img.shields.io/pypi/l/pysimdjson.svg?style=flat-square)
[![CircleCI branch](https://img.shields.io/circleci/project/github/TkTech/pysimdjson/master.svg?style=flat-square)](https://circleci.com/gh/TkTech/pysimdjson)
[![AppVeyor branch](https://img.shields.io/appveyor/ci/TkTech/pysimdjson/master.svg?style=flat-square)](https://ci.appveyor.com/project/TkTech/pysimdjson)

# pysimdjson

Quick-n'dirty Python bindings for [simdjson][] just to see if going down this path
might yield some parse time improvements in real-world applications. So far,
the results are promising, especially when only part of a document is of
interest.

These bindings are currently only tested on OS X & Windows, but should work
everywhere simdjson does although you'll probably have to tweak your build
flags.

See the latest documentation at http://pysimdjson.tkte.ch.

## Installation

There are binary wheels available for py3.6/py3.7 on OS X 10.12 & Windows. On
other platforms you'll need a C++17-capable compiler.

`pip install pysimdjson`

or from source:

```
git clone https://github.com/TkTech/pysimdjson.git
cd pysimdjson
python setup.py install
```

## Example

```python
import simdjson

with open('sample.json', 'rb') as fin:
    doc = simdjson.loads(fin.read())
```

However, this doesn't really gain you that much over, say, ujson. You're still
loading the entire document and converting the entire thing into a series of
Python objects which is very expensive. You can instead use `items()` to pull
only part of a document into Python.

Example document:

```json
{
    "type": "search_results",
    "count": 2,
    "results": [
        {"username": "bob"},
        {"username": "tod"}
    ],
    "error": {
        "message": "All good captain"
    }
}
```

And now lets try some queries...

```python
import simdjson

with open('sample.json', 'rb') as fin:
    # Calling ParsedJson with a document is a shortcut for
    # calling pj.allocate_capacity(<size>) and pj.parse(<doc>). If you're
    # parsing many JSON documents of similar sizes, you can allocate
    # a large buffer just once and keep re-using it instead.
    pj = simdjson.ParsedJson(fin.read())

    pj.items('.type') #> "search_results"
    pj.items('.count') #> 2
    pj.items('.results[].username') #> ["bob", "tod"]
    pj.items('.error.message') #> "All good captain"
```

### AVX2

simdjson requires AVX2 support to function. Check to see if your OS/processor supports it:

- OS X: `sysctl -a | grep machdep.cpu.leaf7_features`
- Linux: `grep avx2 /proc/cpuinfo`

### Low-level interface

You can use the low-level simdjson Iterator interface directly, just be aware
that this interface can change any time. If you depend on it you should pin to
a specific version of simdjson. You may need to use this interface if you're
dealing with odd JSON, such as a document with repeated non-unique keys.

```python
with open('sample.json', 'rb') as fin:
    pj = simdjson.ParsedJson(fin.read())
    iter = simdjson.Iterator(pj)
    if iter.is_object():
        if iter.down():
            print(iter.get_string())
```

## Early Benchmark

Comparing the built-in json module `loads` on py3.7 to simdjson `loads`.

| File | `json` time | `pysimdjson` time |
| ---- | ----------- | ----------------- |
| `jsonexamples/apache_builds.json` | 0.09916733999999999 | 0.074089268 |
| `jsonexamples/canada.json` | 5.305393378 | 1.6547515810000002 |
| `jsonexamples/citm_catalog.json` | 1.3718639709999998 | 1.0438697340000003 |
| `jsonexamples/github_events.json` | 0.04840242700000097 | 0.034239397999998644 |
| `jsonexamples/gsoc-2018.json` | 1.5382746889999996 | 0.9597240750000005 |
| `jsonexamples/instruments.json` | 0.24350973299999978 | 0.13639699600000021 |
| `jsonexamples/marine_ik.json` | 4.505123285000002 | 2.8965093270000004 |
| `jsonexamples/mesh.json` | 1.0325923849999974 | 0.38916503499999777 |
| `jsonexamples/mesh.pretty.json` | 1.7129034710000006 | 0.46509220500000126 |
| `jsonexamples/numbers.json` | 0.16577519699999854 | 0.04843887400000213 |
| `jsonexamples/random.json` | 0.6930746310000018 | 0.6175370539999996 |
| `jsonexamples/twitter.json` | 0.6069602610000011 | 0.41049074900000093 |
| `jsonexamples/twitterescaped.json` | 0.7587005720000022 | 0.41576198399999953 |
| `jsonexamples/update-center.json` | 0.5577604210000011 | 0.4961777420000004 |

Getting subsets of the document is significantly faster. For `canada.json`
getting `.type` using the naive approach and the `items()` appraoch, average
over N=100.

| Python | Time |
| ------ | ---- |
| `json.loads(canada_json)['type']` | 5.76244878 |
| `simdjson.loads(canada_json)['type']` | 1.5984486990000004 |
| `simdjson.ParsedJson(canada_json).items('.type')` | 0.3949587819999998 |

This approach avoids creating Python objects for fields that aren't of
interest. When you only care about a small part of the document, it will always
be faster.

[simdjson]: https://github.com/lemire/simdjson
