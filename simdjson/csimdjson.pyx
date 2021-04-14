# cython: language_level=3, c_string_type=unicode, c_string_encoding=utf8
# distutils: language=c++
import pathlib

from libc.stdint cimport uint64_t, int64_t
from libcpp cimport bool
from libcpp.string cimport string
from cython.operator cimport preincrement, dereference
from cpython.ref cimport Py_INCREF
from cpython.list cimport PyList_New, PyList_SET_ITEM
from cpython.bytes cimport PyBytes_AsStringAndSize
from cpython.slice cimport PySlice_GetIndicesEx, PySlice_New
from cpython.mem cimport PyMem_Malloc, PyMem_Realloc, PyMem_Free
from cpython.buffer cimport PyBuffer_FillInfo

from simdjson.csimdjson cimport *

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


cdef dict object_to_dict(Parser p, simd_object obj, bint recursive):
    cdef:
        dict result = {}
        object pyobj
        size_t size
        const char *data
        simd_object.iterator it = obj.begin()

    while it != obj.end():
        pyobj = element_to_primitive(p, it.value(), recursive)

        data = it.key_c_str()
        size = it.key_length()

        result[data[:size]] = pyobj
        preincrement(it)

    return result


cdef list array_to_list(Parser p, simd_array arr, bint recursive):
    cdef:
        list result = PyList_New(arr.size())
        size_t i = 0

    for element in arr:
        primitive = element_to_primitive(p, element, recursive)
        Py_INCREF(primitive)
        PyList_SET_ITEM(
            result,
            i,
            primitive
        )
        i += 1

    return result


cdef inline element_to_primitive(Parser p, simd_element e,
                                 bint recursive=False):
    cdef:
        const char *data
        size_t size
        element_type type_ = e.type()

    if type_ == element_type.OBJECT:
        if recursive:
            return object_to_dict(p, e.get_object(), recursive)
        return Object.from_element(p, e)
    elif type_ == element_type.ARRAY:
        if recursive:
            return array_to_list(p, e.get_array(), recursive)
        return Array.from_element(p, e)
    elif type_ == element_type.STRING:
        data = e.get_c_str()
        size = e.get_string_length()
        return data[:size]
    elif type_ == element_type.INT64:
        return <int64_t>e
    elif type_ == element_type.UINT64:
        return <uint64_t>e
    elif type_ == element_type.DOUBLE:
        return <double>e
    elif type_ == element_type.BOOL:
        return <bool>e
    elif type_ == element_type.NULL_VALUE:
        return None
    else:
        raise ValueError(  # pragma: no cover
            'Encountered an unknown element_type.'
        )


cdef class ArrayBuffer:
    """
    A container for the flattened data of a homogeneous :class:`Array`.

    .. note::

        This object is responsible for keeping the contents of an Array alive
        even after the simdjson Parser has been reused or destroyed.

    .. admonishment::
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
    cdef readonly Parser parser
    cdef simd_array c_element

    @staticmethod
    cdef inline from_element(Parser parser, simd_element src):
        cdef Array self = Array.__new__(Array)
        self.parser = parser
        self.c_element = src.get_array()
        return self

    def __getitem__(self, key):
        cdef:
            Py_ssize_t start = 0, stop = 0, step = 0, slice_length = 0
            Py_ssize_t dst, src
            list result

        if isinstance(key, slice):
            PySlice_GetIndicesEx(
                key,
                self.c_element.size(),
                &start,
                &stop,
                &step,
                &slice_length
            )

            result = PyList_New(slice_length)
            for dst, src in enumerate(range(start, stop, step)):
                primitive = element_to_primitive(
                    self.parser,
                    self.c_element.at(src),
                    True
                )
                Py_INCREF(primitive)
                PyList_SET_ITEM(
                    result,
                    dst,
                    primitive
                )

            return result
        elif isinstance(key, int):
            # Wrap around negative indexes.
            if key < 0:
                key += self.c_element.size()

        return element_to_primitive(self.parser, self.c_element.at(key))

    def __len__(self):
        return self.c_element.size()

    def __iter__(self):
        cdef simd_array.iterator it = self.c_element.begin()
        while it != self.c_element.end():
            yield element_to_primitive(
                self.parser,
                dereference(it),
                False
            )
            preincrement(it)

    def at_pointer(self, json_pointer):
        """Get the value at the given JSON pointer."""
        return element_to_primitive(
            self.parser,
            self.c_element.at_pointer(
                str_as_bytes(json_pointer)
            )
        )

    def as_list(self):
        """
        Convert this Array to a regular python list, recursively
        converting any objects/lists it finds.
        """
        return array_to_list(self.parser, self.c_element, True)

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
            data. Thus, it's safe to use even after the Array or Paser are
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

    @property
    def slots(self):
        """Returns the number of 'slots' consumed by this array.

        This is not the same thing as `len(array)`, but the number of
        64bit elements consumed by this Array and all of its children
        on the simdjson structure tape.
        """
        return self.c_element.number_of_slots()


cdef class Object:
    """A proxy object that behaves much like a real `dict()`.

    Python objects are not created until an element in the Object
    is accessed. When you only need a subset of an Object, this can be much
    faster than converting an entire Object (and all of its children) into real
    Python objects.
    """
    cdef readonly Parser parser
    cdef simd_object c_element

    @staticmethod
    cdef inline from_element(Parser parser, simd_element src):
        cdef Object self = Object.__new__(Object)
        self.parser = parser
        self.c_element = src.get_object()
        return self

    def __getitem__(self, key):
        return element_to_primitive(
            self.parser,
            self.c_element[str_as_bytes(key)]
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
        try:
            self.c_element[str_as_bytes(key)]
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
            yield element_to_primitive(self.parser, it.value(), True)
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
                element_to_primitive(self.parser, it.value(), True)
            )
            preincrement(it)

    def at_pointer(self, json_pointer):
        """Get the value at the given JSON pointer."""
        return element_to_primitive(
            self.parser,
            self.c_element.at_pointer(
                str_as_bytes(json_pointer)
            )
        )

    def as_dict(self):
        """
        Convert this `Object` to a regular python dictionary,
        recursively converting any objects or lists it finds.
        """
        return object_to_dict(self.parser, self.c_element, True)

    @property
    def mini(self):
        """
        Returns the minified JSON representation of this Object.

        :rtype: bytes
        """
        return <bytes>minify(self.c_element)


cdef class Parser:
    """
    A `Parser` instance is used to load a JSON document.

    A Parser can be reused to parse multiple documents, in which
    case it wil reuse its internal buffer, only increasing it if
    needed.
    The :class:`~Object` and :class:`~Array` objects returned by
    a Parser are invalidated when a new document is parsed.

    :param max_capacity: The maximum size the internal buffer can
                         grow to. [default: SIMDJSON_MAXSIZE_BYTES]
    """
    cdef simd_parser *c_parser

    def __cinit__(self, size_t max_capacity=SIMDJSON_MAXSIZE_BYTES):
        self.c_parser = new simd_parser(max_capacity)

    def __dealloc__(self):
        del self.c_parser

    def parse(self, src not None, bint recursive=False):
        """Parse the given JSON document.

        This method will accept either a ``str``, or any object supporting the
        buffer protocol. This means ``bytes``, ``bytearray``, ``memoryview``,
        etc...

        :param src: The document to parse.
        :param recursive: Recursively turn the document into real
                          python objects instead of pysimdjson proxies.
                          [default: False]
        """
        cdef:
            const unsigned char[::1] data
            const char* str_data = NULL
            Py_ssize_t str_size = 0

        if isinstance(src, str):
            # Sadly memoryview(<unicode>) doesn't work as you'd expect it
            # to even with a default encoding provided.
            str_data = PyUnicode_AsUTF8AndSize(src, &str_size)
            return element_to_primitive(
                self,
                self.c_parser.parse(
                    str_data,
                    str_size,
                    True
                ),
                recursive
            )
        else:
            # Handle any type that provides the buffer API (bytes, bytearray,
            # memoryview, etc)
            data = src

            return element_to_primitive(
                self,
                self.c_parser.parse(
                    <const char*>&data[0],
                    data.shape[0],
                    True
                ),
                recursive
            )

    def load(self, path, bint recursive=False):
        """Load a JSON document from the file system path `path`.

        :param path: A filesystem path.
        :param recursive: Recursively turn the document into real
                          python objects instead of pysimdjson proxies.
        """
        if isinstance(path, unicode):
            path = (<unicode>path).encode('utf-8')
        elif isinstance(path, pathlib.Path):
            path = str(path).encode('utf-8')

        cdef simd_element document = self.c_parser.load(path)
        return element_to_primitive(self, document, recursive)

    @property
    def implementations(self):
        """
        A list of available parser implementations in the form of [(name,
        description),…].
        """
        for implementation in available_implementations:
            yield (implementation.name(), implementation.description())

    @property
    def implementation(self):
        """
        The active parser implementation as (name, description). Can be
        any value from :py:attr:`implementations`. The best implementation
        for your current platform will be picked by default.

        Can be set to the name of any valid implementation to globally
        change the Parser implementation.

        .. warning::
            Setting this to an implementation inappropriate for your platform
            WILL cause illegal instructions or segfaults at best. It's up to
            you to ensure an implementation is valid for your CPU.
        """
        return (
            active_implementation.name(),
            active_implementation.description()
        )

    @implementation.setter
    def implementation(self, name):
        global active_implementation

        for implementation in available_implementations:
            if implementation.name() == str_as_bytes(name):
                active_implementation = implementation
                return

        raise ValueError('Unknown implementation')
