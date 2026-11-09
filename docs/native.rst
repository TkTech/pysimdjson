Native API
==========

.. currentmodule:: simdjson

The native simdjson API offers significant performance improvements over the
builtin-compatible API if only part of a document is of interest.

Objects and arrays are returned as fake dicts (:class:`~Object`) and lists
(:class:`~Array`) that delay the creation of Python objects until they are
accessed.

Duplicate object keys
---------------------

The native :class:`Object` proxy preserves duplicate keys in the JSON document.
Key lookup, ``get()``, and JSON pointer lookup return the first matching value.
Iteration through ``keys()``, ``values()``, and ``items()`` includes every field,
and ``len()`` counts fields, including duplicates.

Converting to Python dictionaries with ``as_dict()``, ``recursive=True``, or
``simdjson.load()`` / ``simdjson.loads()`` keeps the last value for each key,
as the standard library's JSON decoder does. For example, with
``{"a": 1, "a": 2}``, the proxy's ``obj['a']`` is ``1`` and ``len(obj)`` is ``2``,
while ``obj.as_dict()`` is ``{'a': 2}``.

Classes
-------

.. autoclass:: Parser
   :members:

.. autoclass:: Array
   :members:

.. autoclass:: Object
   :members:

Constants
---------

.. py:data:: MAXSIZE_BYTES
   :type: int
   :value: 4294967295

   The maximum document size (in bytes) supported by simdjson.

.. py:data:: PADDING
   :type: int
   :value: 32

   The amount of padding needed in a buffer to parse JSON.

   In general, pysimdjson takes care of padding for you and you do not need
   to worry about this.

.. py:data:: VERSION
   :type: str

   The version of the embedded simdjson library.
