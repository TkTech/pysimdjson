Development
===========

Development requires Python 3.11+ and a C++11-compatible compiler. On Windows,
install Visual Studio C++ build tools for your target architecture and use the
`Developer Command Prompt`_.

Install uv with ``python -m pip install uv``, then install the development
and testing dependencies:

.. code-block:: console

    uv sync --group dev

To rebuild the extension and run the tests:

.. code-block:: console

    uv run --group dev --reinstall-package pysimdjson pytest

Add ``--runslow`` to include the slow integration tests.

Building the extension
----------------------

pysimdjson is written using `Cython`_. The extension is declared in
``pyproject.toml`` and built by setuptools, which installs Cython in an isolated
build environment. ``uv sync`` installs the project in editable mode by default.
Python source changes are visible immediately. After changing Cython or C++
sources, rebuild and reinstall the extension:

.. code-block:: console

    uv sync --group dev --reinstall-package pysimdjson

To build the documentation:

.. code-block:: console

    uv run --group dev make -C docs html

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
