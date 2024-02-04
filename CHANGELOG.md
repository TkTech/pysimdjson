# Changelog

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
