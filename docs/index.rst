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
   contrib/changelog.rst
   license

Python bindings for the `simdjson`_ project, a SIMD-accelerated JSON parser.
If SIMD instructions are unavailable a fallback parser is used, making
pysimdjson safe to use anywhere.

Bindings are currently tested on OS X, Linux, and Windows for Python version
3.6 to 3.9.

Installation
------------

If binary wheels are available for your platform, you can install from pip
with no further requirements:

.. code::

    pip install pysimdjson

Binary wheels are available for the following:

+-------------+-------+-------+-------+-------+
|             |     x86_64            |  ARM  |
+-------------+-------+-------+-------+-------+
| Interpreter | OS X  |  Win  | Linux | Linux |
+=============+=======+=======+=======+=======+
| CPython 3.6 | Yes   | Yes   | Yes   | Yes   |
+-------------+-------+-------+-------+-------+
| CPython 3.7 | Yes   | Yes   | Yes   | Yes   |
+-------------+-------+-------+-------+-------+
| CPython 3.8 | Yes   | Yes   | Yes   | Yes   |
+-------------+-------+-------+-------+-------+
| CPython 3.9 | Yes   | Yes   | Yes   | Yes   |
+-------------+-------+-------+-------+-------+

When binary wheels are not available, a C++11 (or better) compiler is required
when installing.

If you would prefer to always install pysimdjson from source even when
pre-compiled binaries are available, use:

.. code::

    pip install pysimdjson --no-binary :all:

.. admonition:: Packages
   :class: tip

   pysimdjson is also available from unofficial packages contributed by the
   community. You can currently get it from Gentoo and conda-forge. Note these
   may lag behind in releases.

.. _simdjson: https://github.com/simdjson/simdjson
.. _LICENSE: https://github.com/tktech/pysimdjson/blob/master/LICENSE
