Native API
==========

.. currentmodule:: simdjson

The native simdjson API offers significant performance improvements over the
builtin-compatible API, especially if only part of a document is of interest.
Objects and arrays are returned as fake dicts (:class:`~Object`) and lists
(:class:`~Array`) that delay the creation of Python objects until they are
accessed.

.. autoclass:: Parser
   :members:

   .. py:data:: implementations

        A list of available parser implementations in the form of
        `[(name, description),...]`.

   .. py:data:: implementation

        The active parser implementation as (name, description). Can be
        any value from :py:attr:`implementations`. The best implementation
        for your current platform will be picked by default.

        Can be set to the name of any valid implementation to globally
        change the Parser implementation.

        .. warning::
            Setting this to an implementation inappropriate for your platform
            WILL cause illegal instructions or segfaults at best. It's up to
            you to ensure an implementation is valid for your CPU.

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

.. py:data:: DEFAULT_MAX_DEPTH
   :type: int
   :value: 1024

   The maximum number of nested objects and arrays.

.. py:data:: VERSION
   :type: str

   The version of the embedded simdjson library.
