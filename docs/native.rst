Native API
==========

.. currentmodule:: simdjson

The native simdjson API offers significant performance improvements over the
builtin-compatible API if only part of a document is of interest.

Objects and arrays are returned as fake dicts (:class:`~Object`) and lists
(:class:`~Array`) that delay the creation of Python objects until they are
accessed.

Proxies and iterators remain valid after parser reuse or destruction. Each
retains its entire document until the last reference is released. Documents
are not cached.

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

.. _streaming-records:

Streaming records
-----------------

``parse_many()`` reads NDJSON from memory; ``load_many()`` reads a path or binary
file. Both return a :class:`DocumentStream` yielding ordinary Python values.
Each nonblank line must contain one complete JSON value. LF and CRLF are
supported, and the final newline is optional. Invalid or oversized records
raise ``ValueError`` during iteration.

.. code:: python

    import simdjson

    with simdjson.load_many('records.ndjson') as records:
        for record in records:
            process(record)

``batch_size`` must be between 32 and ``max_capacity`` bytes.
Each nonblank line must be smaller than this in UTF-8 bytes, including whitespace
but excluding LF/CRLF and an initial BOM. Blank lines have no size limit.
``parse_many()`` copies the entire input; ``load_many()`` uses buffers proportional
to ``batch_size``.

.. autofunction:: simdjson.parse_many
.. autofunction:: simdjson.load_many

Classes
-------

.. autoclass:: Parser
   :members:

.. autoclass:: Array
   :members:

.. autoclass:: Object
   :members:

.. autoclass:: DocumentStream
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
