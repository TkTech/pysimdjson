Drop-in API
===========

.. module:: simdjson

These methods are provided as drop-in replacements to the built-in JSON module.
They sacrifice some of the speed provided by the :class:`~Parser` interface in
exchange for "just working".

.. autofunction:: load
.. autofunction:: loads

.. note::

    The dump and dumps module are currently just aliased to the built-in JSON
    serializer.

.. autofunction:: dump
.. autofunction:: dumps
