# cython: language_level=3, c_string_type=unicode, c_string_encoding=utf8
# distutils: language=c++
from cython.operator cimport preincrement, dereference  # noqa
from libcpp.memory cimport shared_ptr, make_shared
from cpython.ref cimport Py_INCREF
from cpython.list cimport PyList_New, PyList_SET_ITEM
from cpython.dict cimport PyDict_SetItem
from cpython.bytes cimport PyBytes_AsStringAndSize
from cpython.bytearray cimport PyByteArray_AsString, PyByteArray_Size
from cpython.unicode cimport PyUnicode_AsUTF8AndSize

from simdjson.csimdjson cimport *  # noqa

MAXSIZE_BYTES = SIMDJSON_MAXSIZE_BYTES
PADDING = SIMDJSON_PADDING
VERSION = (
    f'{SIMDJSON_VERSION_MAJOR}.'
    f'{SIMDJSON_VERSION_MINOR}.'
    f'{SIMDJSON_VERSION_REVISION}'
)


cdef inline bytes str_as_bytes(s):
    if isinstance(s, unicode):
        return (<unicode>s).encode('utf-8')
    return s


cdef dict object_to_dict(simd_object obj):
    cdef:
        dict result = {}
        object pyobj
        size_t size
        const char *data
        simd_object.iterator it = obj.begin()

    while it != obj.end():
        pyobj = element_to_primitive(it.value())

        data = it.key_c_str()
        size = it.key_length()

        PyDict_SetItem(
            result,
            unicode_from_str(data, size),
            pyobj
        )

        preincrement(it)

    return result


cdef list array_to_list(simd_array arr):
    cdef:
        list result = PyList_New(arr.size())
        size_t i = 0

    for element in arr:
        primitive = element_to_primitive(element)
        Py_INCREF(primitive)
        PyList_SET_ITEM(
            result,
            i,
            primitive
        )
        i += 1

    return result


cdef inline object element_to_primitive(simd_element e):
    cdef:
        const char *data
        size_t size
        element_type type_ = e.type()

    if type_ == element_type.OBJECT:
        return object_to_dict(e.get_object())
    elif type_ == element_type.ARRAY:
        return array_to_list(e.get_array())
    elif type_ == element_type.STRING:
        data = e.get_c_str()
        size = e.get_string_length()
        return unicode_from_str(data, size)
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

cdef inline error_check(error_code result):
    if result == error_code.SUCCESS:
        return
    elif result == error_code.NO_SUCH_FIELD:
        raise KeyError(error_message(result))
    elif result == error_code.INDEX_OUT_OF_BOUNDS:
        raise IndexError(error_message(result))
    elif result == error_code.INCORRECT_TYPE:
        raise TypeError(error_message(result))
    elif result == error_code.MEMALLOC:
        raise MemoryError(error_message(result))
    elif result == error_code.IO_ERROR:
        raise IOError(error_message(result))
    elif result == error_code.UTF8_ERROR:
        raise UnicodeDecodeError(
            'utf-8',
            b'',
            0,
            0,
            error_message(result)
        )
    else:
        raise ValueError(error_message(result))


cdef class Document:
    cdef simd_document c_document

    def __init__(self):
        self.c_document = simd_document()

    @property
    def root(self):
        """
        The root JSON element of the document.

        :returns: The root JSON element of the document.
        :rtype: object
        """
        return element_to_primitive(self.c_document.root())

    @property
    def as_object(self):
        """
        Get the JSON document as a Python object.

        :returns: The JSON document as a Python object.
        :rtype: object
        """
        return element_to_primitive(self.c_document.root())

    @property
    def capacity(self):
        """
        The current capacity of the internal buffer.

        :returns: The current capacity of the internal buffer.
        :rtype: int
        """
        return self.c_document.capacity()

    def allocate(self, size_t capacity):
        """
        Resize internal buffers to the specified capacity. Once used, any
        existing parsed document is lost.

        If the new capacity is 0, all internal buffers will be freed.

        :param capacity: The new capacity to allocate.
        :raises MemoryError: If the new capacity cannot be allocated.
        :raises RuntimeError: If the new capacity cannot be allocated for an
                              unknown reason.
        """
        cdef error_code result = self.c_document.allocate(capacity)
        if result == error_code.SUCCESS:
            return
        elif result == error_code.MEMALLOC:
            raise MemoryError(
                'Failed to allocate a new buffer with the given capacity.'
            )
        else:
            # Currently, the simdjson implementation of allocate() can only
            # return SUCCESS or MEMALLOC, but we'll leave this here in case.
            raise RuntimeError(
                'Failed to adjust buffer capacity for an unknown reason.'
            )

    def at_pointer(self, char* pointer):
        """
        Get the JSON element at the given JSON Pointer as a Python object.

        :param pointer: A JSON Pointer to the element to retrieve.
        :returns: The element at the given pointer.
        :rtype: object
        """
        cdef simd_element root = self.c_document.root()
        return element_to_primitive(root.at_pointer(pointer))


cdef class Parser:
    """
    A `Parser` instance is used to load and/or parse a JSON document.

    A Parser can be reused to parse multiple documents, in which case it wil
    reuse its internal buffer, only increasing it if needed.

    :param max_capacity: The maximum size the internal buffer can
                         grow to. [default: SIMDJSON_MAXSIZE_BYTES]
    """
    # Keep a reference to our underlying simdjson parser to prevent it being
    # freed while we still have proxy objects pointing to it.
    cdef shared_ptr[simd_parser] c_parser
    # This is a unique ID that is incremented every time the parser is reset.
    cdef unsigned long long valid_id

    def __cinit__(self, size_t max_capacity=SIMDJSON_MAXSIZE_BYTES):
        self.c_parser = make_shared[simd_parser](max_capacity)

    def __dealloc__(self):
        self.c_parser.reset()

    def parse(self, src not None, Document doc = None):
        """Parse the given JSON document.

        The source JSON may be a `str`, `bytes`, `bytearray`, or any other
        object that implements the buffer protocol.

        .. admonition:: Performance
            :class: tip

            While you can pass quite a few things to this method to be parsed,
            simple ``bytes`` will almost always be the fastest.

        :param src: The JSON document to parse.
        :param doc: An optional `Document` instance to reuse.
        :returns: A parsed `Document` instance.
        :rtype: Document
        """
        cdef:
            char *data = NULL
            const char *const_data = NULL
            const uint8_t[::1] typed_memory_view
            Py_ssize_t size = 0
            error_code result
            simd_element root

        if doc is None:
            doc = Document()

        if isinstance(src, bytes):
            PyBytes_AsStringAndSize(src, &data, &size)

            result = dereference(self.c_parser).parse_into_document(
                doc.c_document,
                <const uint8_t *>data,
                size,
                1
            ).get(root)
        elif isinstance(src, str):
            const_data = PyUnicode_AsUTF8AndSize(src, &size)

            result = dereference(self.c_parser).parse_into_document(
                doc.c_document,
                <const uint8_t *>const_data,
                size,
                1
            ).get(root)
        elif isinstance(src, bytearray):
            const_data = PyByteArray_AsString(src)
            size = PyByteArray_Size(src)

            result = dereference(self.c_parser).parse_into_document(
                doc.c_document,
                <const uint8_t *>const_data,
                size,
                1
            ).get(root)
        else:
            # Fallback to using Cython's typed memoryviews to handle pretty
            # much anything that implements the buffer protocol.
            typed_memory_view = src

            # This isn't a great error message, but it's identical to the
            # one that simdjson would raise if given an empty source document.
            if len(typed_memory_view) == 0:
                raise ValueError('EMPTY: no JSON found')

            result = dereference(self.c_parser).parse_into_document(
                doc.c_document,
                &typed_memory_view[0],
                len(typed_memory_view),
                1
            ).get(root)

        error_check(result)
        return doc

    # This is kept here as an example. Cython's typed memoryviews are very
    # convenient, but they are also very slow. Using them here results in an
    # unacceptable level of overhead for trivial parsing tasks.
    #
    # cdef inline _parse(self, const uint8_t[:] src, Document doc):
    #     cdef:
    #         error_code result,
    #         simd_element root

    #     result = dereference(self.c_parser).parse_into_document(
    #         doc.c_document,
    #         &src[0],
    #         len(src),
    #         1
    #     ).get(root)

    #     if result != error_code.SUCCESS:
    #         raise ValueError(error_message(result))

    def load(self, path):
        """Load and parse the given JSON document.

        :param path: The path to the JSON document to load.
        :returns: A parsed `Document` instance.
        :rtype: Document
        """
        with open(path, 'rb') as f:
            return self.parse(f.read())

    def get_implementations(self, supported_by_runtime=True):
        """
        A list of available parser implementations in the form of [(name,
        description),…].

        By default, this only returns the implementations that are usable on
        the current runtime. Setting `supported_by_runtime` to False will
        instead return all the implementations _compiled_ into this build of
        simdjson.

        :param supported_by_runtime: Whether to only return implementations
                                     that are usable on the current runtime.
                                     [default: True]
        :returns: A list of available parser implementations.
        :rtype: list
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

        :returns: The active parser Implementation as (name, description).
        :rtype: tuple
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
                    'Attempted to set a runtime Implementation that is not'
                    'supported on the current host.'
                )

            set_active_implementation(impl)
            return

        raise ValueError('Unknown Implementation')
