# Changelog

## 7.0.2

- Remove self-dependency in the pyproject.toml, fixing poetry installs (#130)

## 7.0.1

- Ensure csimdjson.pxd is included in the sdist (#129)

## 7.0.0

- Drop python 3.8, pypy builds, add python 3.13 (#117, #123)
- Add proper .load/.loads type signatures (#116)
- Updating and modernize github actions, simplify packaging and CI.
- Update upstream simdjson to 3.12.3.
- Add alias to json.JSONEncoder to drop-in API. (#118)
- Deterministic build / static build metadata

## 6.0.0

- Dropped support for CPython 3.6 - 3.8 which are long past their support window,
  added support for CPython for 3.11 & 3.12.
- Updated upstream simdjson library to 3.6.4.
- Various packaging, CI, and compiler version bumps.

## 5.0.1

- Expanded PyPy prebuilt binary support (packaging change only).

## 5.0.0

- Updated upstream simdjson library to 2.0.1, which brings AVX-512 support.
- `Parser.implementations` property replaced with `Parser.get_implementations`
  to support optionally filtering to just the ones supported by the current
  runtime.

## 4.0.3

- Updated upstream simdjson library to 1.0.2.
- Binary wheels are now tested and available for py3.6-py3.10 on x86[_64],
  ppc64le and aarch64.
  - Under Linux, wheels are built for both manylinux and musl (Alpine).
  - Under Linux, wheels are also available for PyPy3.7.
- Minor documentation fixes.
