# cython: language_level=3, c_string_type=unicode, c_string_encoding=utf8
# distutils: language=c++
import os
import weakref
from contextlib import ExitStack

from cython.operator cimport preincrement, dereference  # noqa
from libcpp.memory cimport unique_ptr
from cpython.ref cimport Py_INCREF
from cpython.list cimport PyList_New, PyList_SET_ITEM
from cpython.bytes cimport PyBytes_AsStringAndSize
from cpython.slice cimport PySlice_GetIndicesEx, PySlice_New
from cpython.mem cimport PyMem_Free
from cpython.number cimport PyNumber_AsSsize_t
from cpython.buffer cimport PyBuffer_FillInfo

from simdjson.csimdjson cimport *  # noqa

MAXSIZE_BYTES = SIMDJSON_MAXSIZE_BYTES
PADDING = SIMDJSON_PADDING
VERSION = (
    f'{SIMDJSON_VERSION_MAJOR}.'
    f'{SIMDJSON_VERSION_MINOR}.'
    f'{SIMDJSON_VERSION_REVISION}'
)


cdef bytes str_as_bytes(s):
    if isinstance(s, unicode):
        return (<unicode>s).encode('utf-8')
    return s


cdef class _Document:
    # Native elements point into this document, so its address must stay fixed.
    # Every proxy holds this Python owner; no parser or cache owns it.
    cdef simd_document document
    cdef object parser_ref


cdef dict object_to_dict(_Document owner, simd_object obj, bint recursive):
    cdef:
        dict result = {}
        object pyobj
        size_t size
        const char *data
        simd_object.iterator it = obj.begin()

    while it != obj.end():
        pyobj = element_to_primitive(owner, it.value(), recursive)

        data = it.key_c_str()
        size = it.key_length()

        result[data[:size]] = pyobj
        preincrement(it)

    return result


cdef list array_to_list(_Document owner, simd_array arr, bint recursive):
    cdef:
        list result = PyList_New(arr.size())
        size_t i = 0

    for element in arr:
        primitive = element_to_primitive(owner, element, recursive)
        Py_INCREF(primitive)
        PyList_SET_ITEM(
            result,
            i,
            primitive
        )
        i += 1

    return result


cdef inline object element_to_primitive(_Document owner, simd_element e,
                                        bint recursive=False):
    cdef:
        const char *data
        size_t size
        element_type type_ = e.type()

    if type_ == element_type.OBJECT:
        if recursive:
            return object_to_dict(owner, e.get_object(), recursive)
        return Object.from_element(owner, e)
    elif type_ == element_type.ARRAY:
        if recursive:
            return array_to_list(owner, e.get_array(), recursive)
        return Array.from_element(owner, e)
    elif type_ == element_type.STRING:
        data = e.get_c_str()
        size = e.get_string_length()
        return data[:size]
    elif type_ == element_type.INT64:
        return e.get_int64()
    elif type_ == element_type.UINT64:
        return e.get_uint64()
    elif type_ == element_type.DOUBLE:
        return e.get_double()
    elif type_ == element_type.BOOL:
        return e.get_bool()
    elif type_ == element_type.NULL_VALUE:
        return None
    else:
        raise ValueError(  # pragma: no cover
            'Encountered an unknown element_type.'
        )


cdef class ArrayBuffer:
    """
    A container for the flattened data of a homogeneous :class:`Array`.

    .. admonition::
        :class: note

        This object is responsible for keeping the contents of an Array alive
        even after the simdjson Parser has been reused or destroyed.

    .. admonition::
       :class: warning

       You should never create this class on your own. It is created and
       returned for you by :func:`Array.as_buffer`.
    """
    cdef void *buffer
    cdef readonly size_t size

    def __cinit__(self):
        self.buffer = NULL
        self.size = 0

    def __dealloc__(self):
        if self.buffer != NULL:
            PyMem_Free(self.buffer)

    @staticmethod
    cdef inline from_element(simd_array src, of_type):
        cdef:
            ArrayBuffer self = ArrayBuffer.__new__(ArrayBuffer)

        if of_type == 'd':
            self.buffer = flatten_array[double](src, &self.size)
        elif of_type == 'i':
            self.buffer = flatten_array[int64_t](src, &self.size)
        elif of_type == 'u':
            self.buffer = flatten_array[uint64_t](src, &self.size)
        else:
            raise ValueError('of_type must be one of {d,i,u}.')

        if not self.buffer:
            raise MemoryError()  # pragma: no cover

        return self

    def __getbuffer__(self, Py_buffer *buffer, int flags):
        PyBuffer_FillInfo(buffer, self, self.buffer, self.size, 0, flags)

    def __releasebuffer__(self, Py_buffer *buffer):
        pass


cdef class Array:
    """A proxy object that behaves much like a real `list()`.

    Python objects are not created until an element in the list is accessed.
    When you only need a subset of an Array, this can be much faster than
    converting an entire array (and all of its children) into real Python
    objects.
    """
    cdef _Document owner
    cdef simd_array c_element

    @staticmethod
    cdef inline from_element(_Document owner, simd_element src):
        cdef Array self = Array.__new__(Array)
        self.owner = owner
        self.c_element = src.get_array()
        return self

    @property
    def parser(self):
        """The originating Parser, or None after it is destroyed."""
        return self.owner.parser_ref()

    def __getitem__(self, key):
        cdef:
            Py_ssize_t start = 0, stop = 0, step = 0, slice_length = 0
            Py_ssize_t dst, src, target, remaining, index
            Py_ssize_t array_size = self.c_element.size()
            simd_array.iterator it
            list result

        if isinstance(key, slice):
            PySlice_GetIndicesEx(
                key,
                array_size,
                &start,
                &stop,
                &step,
                &slice_length
            )

            result = PyList_New(slice_length)
            if slice_length == 0:
                return result

            # Traverse once, even for reverse slices. For negative steps,
            # visit selected elements in ascending order and fill backwards.
            target = start if step > 0 else start + (slice_length - 1) * step
            dst = 0 if step > 0 else slice_length - 1
            remaining = slice_length
            src = 0
            it = self.c_element.begin()
            while remaining:
                if src == target:
                    primitive = element_to_primitive(self.owner, dereference(it), True)
                    Py_INCREF(primitive)
                    PyList_SET_ITEM(result, dst, primitive)
                    remaining -= 1
                    if remaining == 0:
                        break
                    if step > 0:
                        target += step
                        dst += 1
                    else:
                        target -= step
                        dst -= 1
                preincrement(it)
                src += 1

            return result

        index = PyNumber_AsSsize_t(key, IndexError)
        if index < 0:
            index += array_size
        if index < 0 or index >= array_size:
            raise IndexError('array index out of range')
        return element_to_primitive(self.owner, self.c_element.at(<size_t>index))

    def __len__(self):
        return self.c_element.size()

    def __iter__(self):
        cdef simd_array.iterator it = self.c_element.begin()
        while it != self.c_element.end():
            yield element_to_primitive(
                self.owner,
                dereference(it),
                False
            )
            preincrement(it)

    def at_pointer(self, json_pointer):
        """Get the value at the given JSON pointer."""
        cdef bytes pointer_bytes = str_as_bytes(json_pointer)
        return element_to_primitive(
            self.owner,
            self.c_element.at_pointer(
                string_view(<const char*>pointer_bytes, len(pointer_bytes))
            )
        )

    def as_list(self):
        """
        Convert this Array to a regular python list, recursively
        converting any objects/lists it finds.
        """
        return array_to_list(self.owner, self.c_element, True)

    def as_buffer(self, *, of_type):
        """
        **Copies** the contents of a **homogeneous** array to an
        object that can be used as a `buffer`. This means it can be
        used as input for `numpy.frombuffer`, `bytearray`,
        `memoryview`, etc.

        When n-dimensional arrays are encountered, this method will recursively
        flatten them.

        .. note::

            The object returned by this method contains a *copy* of the Array's
            data. Thus, it's safe to use even after the Array or Parser are
            destroyed or reused.

        :param of_type: One of 'd' (double), 'i' (signed 64-bit integer) or 'u'
                        (unsigned 64-bit integer).
        """
        return ArrayBuffer.from_element(self.c_element, of_type)

    @property
    def mini(self):
        """
        Returns the minified JSON representation of this Array.

        :rtype: bytes
        """
        return <bytes>minify(self.c_element)


cdef class Object:
    """A proxy object that behaves much like a real `dict()`.

    Python objects are not created until an element in the Object
    is accessed. When you only need a subset of an Object, this can be much
    faster than converting an entire Object (and all of its children) into real
    Python objects.
    """
    cdef _Document owner
    cdef simd_object c_element

    @staticmethod
    cdef inline from_element(_Document owner, simd_element src):
        cdef Object self = Object.__new__(Object)
        self.owner = owner
        self.c_element = src.get_object()
        return self

    @property
    def parser(self):
        """The originating Parser, or None after it is destroyed."""
        return self.owner.parser_ref()

    def __getitem__(self, key):
        if not isinstance(key, (str, bytes)):
            hash(key)
            raise KeyError(key)
        cdef bytes key_bytes = str_as_bytes(key)
        return element_to_primitive(
            self.owner,
            self.c_element[string_view(<const char*>key_bytes, len(key_bytes))]
        )

    def get(self, key, default=None):
        """
        Return the value of `key`, or `default` if the key does
        not exist.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __len__(self):
        return self.c_element.size()

    def __contains__(self, key):
        if not isinstance(key, (str, bytes)):
            hash(key)
            return False
        cdef bytes key_bytes = str_as_bytes(key)
        try:
            self.c_element[string_view(<const char*>key_bytes, len(key_bytes))]
        except KeyError:
            return False
        return True

    def __iter__(self):
        """
        Returns an iterator over all keys in this `Object`.
        """
        cdef:
            size_t size
            const char *data
            simd_object.iterator it = self.c_element.begin()

        while it != self.c_element.end():
            data = it.key_c_str()
            size = it.key_length()
            yield data[:size]
            preincrement(it)

    keys = __iter__

    def values(self):
        """
        Returns an iterator over of all values in this `Object`.
        """
        cdef simd_object.iterator it = self.c_element.begin()
        while it != self.c_element.end():
            yield element_to_primitive(self.owner, it.value(), True)
            preincrement(it)

    def items(self):
        """
        Returns an iterator over all the (key, value) pairs in this
        `Object`.
        """
        cdef:
            size_t size
            const char *data
            simd_object.iterator it = self.c_element.begin()

        while it != self.c_element.end():
            data = it.key_c_str()
            size = it.key_length()
            yield (
                data[:size],
                element_to_primitive(self.owner, it.value(), True)
            )
            preincrement(it)

    def at_pointer(self, json_pointer):
        """Get the value at the given JSON pointer."""
        cdef bytes pointer_bytes = str_as_bytes(json_pointer)
        return element_to_primitive(
            self.owner,
            self.c_element.at_pointer(
                string_view(<const char*>pointer_bytes, len(pointer_bytes))
            )
        )

    def as_dict(self):
        """
        Convert this `Object` to a regular python dictionary,
        recursively converting any objects or lists it finds.
        """
        return object_to_dict(self.owner, self.c_element, True)

    @property
    def mini(self):
        """
        Returns the minified JSON representation of this Object.

        :rtype: bytes
        """
        return <bytes>minify(self.c_element)


cdef class DocumentStream:
    """An iterator and context manager for NDJSON records."""
    cdef unique_ptr[records] stream
    cdef object file_iterator
    cdef bint running

    def __iter__(self):
        return self

    def __enter__(self):
        if not self.stream and self.file_iterator is None:
            raise ValueError('DocumentStream is closed')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def closed(self):
        """Whether this stream has released its resources."""
        return not self.stream and self.file_iterator is None

    def __next__(self):
        if self.running:
            raise RuntimeError('DocumentStream is already executing')
        if not self.stream and self.file_iterator is None:
            raise StopIteration
        self.running = True
        try:
            if self.file_iterator is not None:
                return next(self.file_iterator)
            return self.stream.get().next()
        except BaseException:
            self.running = False
            self.close()
            raise
        finally:
            self.running = False

    def close(self):
        """Release resources, leaving caller-provided files open."""
        if self.running:
            raise RuntimeError('Cannot close a DocumentStream while it is executing')
        self.running = True
        file_iterator = self.file_iterator
        self.file_iterator = None
        try:
            if file_iterator is not None:
                file_iterator.close()
        finally:
            self.stream.reset()
            self.running = False


def _load_many(source, size_t batch_size, size_t max_capacity):
    # A newline is a safe boundary for NDJSON: it cannot occur inside a valid
    # JSON string. A record crossing a read boundary is carried to the next read.
    cdef unique_ptr[records] stream
    cdef bytes pending = b''
    cdef bytes data, complete, line
    cdef Py_ssize_t boundary
    cdef bint eof
    cdef bint first = True
    stream.reset(new records(batch_size, max_capacity))
    try:
        with ExitStack() as stack:
            if hasattr(source, 'read'):
                fp = source
            else:
                fp = stack.enter_context(open(source, 'rb'))
            while True:
                chunk = fp.read(batch_size)
                if not isinstance(chunk, bytes):
                    raise TypeError('load_many() requires a binary file')
                eof = not chunk
                if not chunk:
                    complete = pending
                    pending = b''
                else:
                    data = pending + chunk
                    boundary = data.rfind(b'\n')
                    if boundary < 0:
                        pending = data
                        if <size_t>len(pending) >= batch_size:
                            line = pending[3:] if first and pending.startswith(b'\xef\xbb\xbf') else pending
                            if not line.strip(b' \t\r'):
                                # Retain enough whitespace to reject a value
                                # appended to this same overlong line later.
                                pending = line[-<Py_ssize_t>batch_size:]
                                first = False
                                continue
                            # A final CR may be the first half of CRLF. Wait
                            # for the next read to distinguish it from data.
                            if <size_t>(len(line) - line.endswith(b'\r')) >= batch_size:
                                raise ValueError('NDJSON record must be smaller than batch_size')
                        continue
                    complete = data[:boundary + 1]
                    pending = data[boundary + 1:]
                if complete:
                    if not first and complete.startswith(b'\xef\xbb\xbf'):
                        raise ValueError('Unexpected UTF-8 BOM inside an NDJSON stream')
                    first = False
                    stream.get().reset(complete, len(complete))
                    # Release Python input copies before yielding results.
                    complete = b''
                    data = b''
                    chunk = b''
                    line = b''
                    while True:
                        try:
                            result = stream.get().next()
                        except StopIteration:
                            break
                        yield result
                        del result
                if eof:
                    return
    finally:
        stream.reset()


cdef class Parser:
    """
    Parse JSON documents while reusing scratch buffers.

    :param max_capacity: Maximum input document size in bytes, not a total-memory limit.
                         [default: SIMDJSON_MAXSIZE_BYTES]
    """
    cdef unique_ptr[simd_parser] c_parser
    cdef size_t max_capacity
    cdef object __weakref__

    def __cinit__(self, size_t max_capacity=SIMDJSON_MAXSIZE_BYTES):
        self.max_capacity = max_capacity
        self.c_parser.reset(new simd_parser(max_capacity))

    def parse(self, src not None, bint recursive=False):
        """Parse the given JSON document.

        The source document may be a `str`, `bytes`, `bytearray`, or any other
        object that implements the buffer protocol.

        .. admonition:: Performance
            :class: tip

            While you can pass quite a few things to this method to be parsed,
            simple ``bytes`` will almost always be the fastest.

        Existing proxies remain valid when the parser is reused or destroyed.

        :param src: The document to parse.
        :param recursive: Recursively turn the document into real
                          python objects instead of pysimdjson proxies.
                          [default: False]
        """
        cdef:
            const unsigned char[::1] data
            const char * str_data = NULL
            char * bytes_data = NULL
            Py_ssize_t str_size = 0
            _Document owner
            simd_element root

        # Normalize inputs before parsing: buffer providers can execute Python
        # code, including another call to this parser.
        if isinstance(src, bytes):
            PyBytes_AsStringAndSize(src, &bytes_data, &str_size)
            str_data = bytes_data
        elif isinstance(src, str):
            str_data = PyUnicode_AsUTF8AndSize(src, &str_size)
        else:
            data = src
            if data.size == 0:
                raise ValueError('EMPTY: no JSON found')
            str_data = <const char*>&data[0]
            str_size = data.shape[0]

        owner = _Document.__new__(_Document)
        owner.parser_ref = weakref.ref(self)
        # This API handles the input boundary safely without a padded copy.
        # Keep the GIL and source buffer alive throughout the native parse.
        root = dereference(self.c_parser).parse_into_document_unpadded(
            owner.document, <const unsigned char*>str_data, str_size
        )
        return element_to_primitive(owner, root, recursive)

    def load(self, path, bint recursive=False):
        """Load a JSON document from the file system path `path`.

        Existing proxies remain valid when the parser is reused or destroyed.

        :param path: A filesystem path.
        :param recursive: Recursively turn the document into real
                          python objects instead of pysimdjson proxies.
        """
        path = os.fspath(path)
        cdef bytes path_bytes = str_as_bytes(path)
        cdef _Document owner = _Document.__new__(_Document)
        owner.parser_ref = weakref.ref(self)
        cdef simd_element root = load_document(
            dereference(self.c_parser), owner.document,
            string_view(<const char*>path_bytes, len(path_bytes))
        )
        return element_to_primitive(owner, root, recursive)

    cdef size_t _batch_size(self, object value) except *:
        cdef Py_ssize_t size = PyNumber_AsSsize_t(value, OverflowError)
        if size < 32 or <size_t>size > self.max_capacity:
            raise ValueError('batch_size must be between 32 and max_capacity')
        return <size_t>size

    def parse_many(self, src not None, *, batch_size=1000000):
        """Parse NDJSON from memory, yielding independent Python values.

        Returns a DocumentStream owning a copy of the input.
        See :ref:`streaming-records` for format and size limits.
        """
        cdef size_t size = self._batch_size(batch_size)
        cdef const unsigned char[::1] data
        cdef bytes encoded
        cdef const char *ptr
        cdef Py_ssize_t length
        cdef DocumentStream result = DocumentStream.__new__(DocumentStream)
        if isinstance(src, str):
            ptr = PyUnicode_AsUTF8AndSize(src, &length)
        elif isinstance(src, bytes):
            encoded = src
            ptr = encoded
            length = len(encoded)
        else:
            data = src
            length = data.shape[0]
            ptr = <const char*>&data[0] if length else <const char*>NULL
        result.stream.reset(new records(size, self.max_capacity))
        result.stream.get().reset(ptr, length)
        return result

    def load_many(self, source, *, batch_size=1000000):
        """Read NDJSON from a path or binary file, yielding independent Python values.

        Returns a DocumentStream using bounded reads; caller-owned files stay open.
        See :ref:`streaming-records` for format and size limits.
        """
        cdef size_t size = self._batch_size(batch_size)
        cdef DocumentStream result = DocumentStream.__new__(DocumentStream)
        result.file_iterator = _load_many(source, size, self.max_capacity)
        return result

    def get_implementations(self, supported_by_runtime=True):
        """
        A list of available parser implementations in the form of [(name,
        description),…].

        By default, this only returns the implementations that are usable on
        the current runtime. Setting `supported_by_runtime` to False will
        instead return all the implementations _compiled_ into this build of
        simdjson.
        """
        for impl in get_available_implementations():
            if supported_by_runtime and not impl.supported_by_runtime_system():
                continue

            yield impl.name(), impl.description()

    @property
    def implementation(self):
        """
        The active parser Implementation as (name, description). Can be
        any value from :py:attr:`implementations`. The best Implementation
        for your current platform will be picked by default.

        Can be set to the name of any valid Implementation to globally
        change underlying Parser Implementation, such as to disable AVX-512
        if it is causing down-clocking.
        """
        cdef const Implementation * impl = (
            <const Implementation *>get_active_implementation()
        )
        return impl.name(), impl.description()

    @implementation.setter
    def implementation(self, name):
        for impl in get_available_implementations():
            if impl.name() != str_as_bytes(name):
                continue

            if not impl.supported_by_runtime_system():
                raise RuntimeError(
                    'Attempted to set a runtime Implementation that is not '
                    'supported on the current host.'
                )

            set_active_implementation(impl)
            return

        raise ValueError('Unknown Implementation')
