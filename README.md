# pysimdjson

Quick-n'dirty Python bindings for [simdjson][] just to see if going down this path
might yield some parse time improvements in real-world applications.

These bindings are currently only tested on OS X, but should work everywhere
simdjson does although you'll probably have to tweak your build flags.

## Example

```
import pysimdjson

with open('sample.json', 'rb') as fin:
    doc = pysimdjson.loads(fin)
```

## AVX2

simdjson requires AVX2 support to function. Check to see if your OS/processor supports it:

OS X: `sysctl -a | grep machdep.cpu.leaf7_features`
Linux: `grep avx2 /proc/cpuinfo`

## Early Benchmark

Comparing the built-in json module on py3.7 to pysimdjson.

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

The overhead of constructing the python dict is immense, as is decoding strings
to python's UTF-8 objects. JSON files that are 99% strings and dicts will see
little improvements, but all others see significant improvement.

Providing an API for iteration without converting the entire document into a
python object would yield significant improvements when you only care about
part of the document.

[simdjson]: https://github.com/lemire/simdjson
