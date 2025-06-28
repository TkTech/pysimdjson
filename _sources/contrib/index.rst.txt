Development
===========

This project comes with a full test suite. To install development and testing
dependencies, use:

.. code::

    pip install -e ".[test]"

To run the tests, just type ``pytest``. To also run some slow integration
tests, use ``pytest --runslow``.

To properly test builds on Windows, you need both a recent version of Visual
Studio as well as VS2015, patch 3. Older versions of CPython required portable
C/C++ extensions to be built with the same version of VS as the interpreter.
Use the `Developer Command Prompt`_ to easily switch between versions.

Cythonize
---------

pysimdjson is written using `Cython`_. However, by default ``setup.py`` will
use the already-generated ``csimdjson.cpp`` instead of regenerating it. This
is to avoid making Cython an install-time requirement.

To force the usage of Cython, use ``BUILD_WITH_CYTHON``:

.. code::

    BUILD_WITH_CYTHON=1 python setup.py develop

This will cause Cython to regenerate the ``csimdjson.cpp`` from the
``csimdjson.pyx`` and ``csimdjson.pxd`` files.

To build pysimdjson with support for linetracing and coverage, use ``BUILD_FOR_DEBUG``:

.. code::

    BUILD_WITH_CYTHON=1 BUILD_FOR_DEBUG=1 python setup.py develop

pysimdjson will also reuse the generated .so file if you build it more than
once, so to force Cython to rebuild it, use ``FORCE_REBUILD``:

.. code::

    BUILD_WITH_CYTHON=1 FORCE_REBUILD=1 python setup.py develop

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