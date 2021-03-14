Development
===========

This project comes with a full test suite. To install development and testing
dependencies, use:

    pip install -e ".[test]"

To also install 3rd party JSON libraries used for running benchmarks, use:

    pip install -e ".[benchmark]"

To run the tests, just type ``pytest``. To also run the benchmarks, use
``pytest --runslow``.

To properly test on Windows, you need both a recent version of Visual Studio as
well as VS2015, patch 3. Older versions of CPython required portable C/C++
extensions to be built with the same version of VS as the interpreter.  Use the
`Developer Command Prompt`_ to easily switch between versions.

.. _Developer Command Prompt: https://docs.microsoft.com/en-us/dotnet/
   framework/tools/developer-command-prompt-for-vs
