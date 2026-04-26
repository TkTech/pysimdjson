Development
===========

This project comes with a full test suite. To install development and testing
dependencies, use:

.. code::

    uv sync --group dev

To run the tests, use ``uv run --group dev --reinstall-package pysimdjson
pytest``. To also run the slow integration tests, use ``uv run --group dev
--reinstall-package pysimdjson pytest --runslow``.

To properly test builds on Windows, you need both a recent version of Visual
Studio as well as VS2015, patch 3. Older versions of CPython required portable
C/C++ extensions to be built with the same version of VS as the interpreter.
Use the `Developer Command Prompt`_ to easily switch between versions.

Cythonize
---------

pysimdjson is written using `Cython`_. The extension module is declared in
``pyproject.toml`` and built by setuptools. ``uv sync`` installs the project in
editable mode by default:

.. code::

    uv sync --group dev

Python source changes are visible immediately. When you change Cython or C++
sources, force uv to rebuild and reinstall the extension:

.. code::

    uv sync --group dev --reinstall-package pysimdjson

To build pysimdjson with support for linetracing and coverage, use
``BUILD_FOR_DEBUG``:

.. code::

    BUILD_FOR_DEBUG=1 uv sync --group dev --reinstall-package pysimdjson

Benchmarks
----------

The benchmarks that used to exist in this project have been moved into a
sister project, `json_benchmark`_. This project contains a number of
benchmarks for various JSON libraries, including pysimdjson. It also tests
for correctness, so it can be used to verify that simdjson is working
correctly.

.. _Developer Command Prompt: https://docs.microsoft.com/en-us/dotnet/
   framework/tools/developer-command-prompt-for-vs
.. _Cython: https://cython.readthedocs.io/en/latest/
.. _json_benchmark: https://github.com/tktech/json_benchmark
