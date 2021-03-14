pysimdjson
==========

.. toctree::
   :caption: Contents:
   :hidden:
   :maxdepth: 4
   :titlesonly:

   self
   performance
   dropin
   native

.. toctree::
   :caption: Development:
   :hidden:

   contrib/index.rst
   license


Python bindings for the `simdjson`_ project, a SIMD-accelerated JSON parser.
If SIMD instructions are unavailable a fallback parser is used, making
pysimdjson safe to use anywhere.

Bindings are currently tested on OS X, Linux, and Windows for Python version
3.5 to 3.9.

Installation
------------

If binary wheels are available for your platform, you can install from pip
with no further requirements:

    pip install pysimdjson

Binary wheels are available for the following:

+-------------+-------+-------+-------+-------+
|             |     x86_64            |  ARM  |
+-------------+-------+-------+-------+-------+
| Interpreter | OS X  |  Win  | Linux | Linux |
+=============+=======+=======+=======+=======+
| CPython 3.5 | Yes   | Yes   | Yes   | Yes   |
+-------------+-------+-------+-------+-------+
| CPython 3.6 | Yes   | Yes   | Yes   | Yes   |
+-------------+-------+-------+-------+-------+
| CPython 3.7 | Yes   | Yes   | Yes   | Yes   |
+-------------+-------+-------+-------+-------+
| CPython 3.8 | Yes   | Yes   | Yes   | Yes   |
+-------------+-------+-------+-------+-------+
| CPython 3.9 | Yes   | Yes   | Yes   | Yes   |
+-------------+-------+-------+-------+-------+
| pypy3       | Yes   | No    | No    | No    |
+-------------+-------+-------+-------+-------+

When binary wheels are not available, a C++11 (or better) compiler is required
when installing.

To ensure you're getting the best optimizations available for your platform,
you can force a build from source:

    pip install pysimdjson --no-binary :all:

License
-------

pysimdjson is made available under the MIT License. For more details, see
`LICENSE`_.


.. _simdjson: https://github.com/simdjson/simdjson
.. _LICENSE: https://github.com/tktech/pysimdjson/blob/master/LICENSE
