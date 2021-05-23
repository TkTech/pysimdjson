Changelog
=========

Version 4.0.0
-------------

Changes:

- Completely rewritten from the ground up, switching from pybind11 (back) to
  Cython due to unacceptable overhead on function calls.
- New project logo!
- Typings (thanks kornicameister!)
- Python 3.5 support has been removed (here we come f-strings!)
- Official pypy3 support has been temporarily removed (due to memory safety
  concerns with PyPy's delayed __del__). Still works if you build yourself
  and re-use the Parser with care. Are you a pypy expert? We could use your
  help!
- Using `as_buffer()` will now always return a buffer typed as a flat array
  of bytes.
- Array.slots() has been removed. As we prepare to support the simdjson
  On-Demand and future streaming API, details specific to the DOM API will be
  removed and/or abstracted.

Bugfixes:

- Enforces the simdjson document lifecycle, preventing the unsafe usage of
  Object or Array when parsers are re-used.
- Prevents Parser instances from going out of scope when an Object or Array

Deprecation:

- Python 3.6 support will be removed with the next major release, so that we
  can take advantage of new features in 3.7 (PEP 562, insert-order-dict, PEP
  539) for future work.
