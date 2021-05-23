Development
===========

This project comes with a full test suite. To install development and testing
dependencies, use:

.. code::

    pip install -e ".[test]"

To also install 3rd party JSON libraries used for running benchmarks, use:

.. code::

    pip install -e ".[benchmark]"

To run the tests, just type ``pytest``. To also run the benchmarks, use
``pytest --runslow``. ``--runslow`` will also run the NumPy integration tests.

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

.. _Developer Command Prompt: https://docs.microsoft.com/en-us/dotnet/
   framework/tools/developer-command-prompt-for-vs
.. _Cython: https://cython.readthedocs.io/en/latest/
