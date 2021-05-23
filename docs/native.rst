Native API
==========

.. currentmodule:: simdjson

The native simdjson API offers significant performance improvements over the
builtin-compatible API if only part of a document is of interest.

Objects and arrays are returned as fake dicts (:class:`~Object`) and lists
(:class:`~Array`) that delay the creation of Python objects until they are
accessed.

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
