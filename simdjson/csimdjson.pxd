# cython: language_level=3
# distutils: language=c++
from libc.stdint cimport uint32_t, uint64_t, int64_t
from libcpp.string cimport string

cdef extern from "Python.h":
    # Correct signature is const, but this was only fixed in Py3.7+
    cdef char* PyUnicode_AsUTF8AndSize(object, Py_ssize_t *)

cdef extern from "util.h":
    cdef void simdjson_error_handler()
    cdef void * flatten_array[T](simd_array src) \
        except +simdjson_error_handler


cdef extern from "simdjson.h" namespace "simdjson":
    cdef size_t SIMDJSON_MAXSIZE_BYTES
    cdef size_t SIMDJSON_PADDING
    cdef enum:
        SIMDJSON_VERSION_MAJOR
        SIMDJSON_VERSION_MINOR
        SIMDJSON_VERSION_REVISION

    cdef string minify[T](T) except +simdjson_error_handler

    cdef cppclass implementation:
        const string &name()
        const string &description()

    # This is marked as private and internal, but we don't have a choice.
    cdef cppclass available_implementation_list "simdjson::internal":
        const implementation * const * begin()
        const implementation * const * end()

        const implementation * operator[](string)

    implementation * active_implementation
    available_implementation_list available_implementations

cdef extern from "simdjson.h" namespace "simdjson::dom::element_type":
    cdef enum element_type "simdjson::dom::element_type":
        OBJECT,
        ARRAY,
        STRING,
        INT64,
        UINT64,
        DOUBLE,
        BOOL,
        NULL_VALUE

# There has to be a better way of defining a default exception handler. Maybe a
# 'except +' syntax on the cdef cppclass? If there is, it isn't documented.
cdef extern from "simdjson.h" namespace "simdjson::dom":
    cdef cppclass simd_array "simdjson::dom::array":
        cppclass iterator:
            iterator()

            iterator operator++()
            bint operator!=(iterator)
            simd_element operator*()

        iterator begin()
        iterator end()

        size_t size()
        size_t number_of_slots()

        simd_element at(int) except +simdjson_error_handler
        simd_element at_pointer(const char*) except +simdjson_error_handler

    cdef cppclass simd_object "simdjson::dom::object":
        cppclass iterator:
            iterator()

            iterator operator++()
            bint operator!=(iterator)

            uint32_t key_length()
            const char *key_c_str()
            simd_element value()

        iterator begin()
        iterator end()

        size_t size()

        simd_element at_pointer(const char*) except +simdjson_error_handler
        simd_element operator[](const char*) except +simdjson_error_handler

    cdef cppclass simd_element "simdjson::dom::element":
        element_type type() except +simdjson_error_handler

        const char *get_c_str() except +simdjson_error_handler
        size_t get_string_length() except +simdjson_error_handler

        simd_array get_array() except +simdjson_error_handler
        simd_object get_object() except +simdjson_error_handler
        int64_t get_int64() except +simdjson_error_handler
        uint64_t get_uint64() except +simdjson_error_handler
        double get_double() except +simdjson_error_handler
        bint get_bool() except +simdjson_error_handler

    cdef cppclass simd_parser "simdjson::dom::parser":
        simd_parser() except +simdjson_error_handler
        simd_parser(size_t max_capacity) except +simdjson_error_handler

        simd_element parse(const char *, size_t, bool) \
            except +simdjson_error_handler
        simd_element load(const char *) except +simdjson_error_handler
