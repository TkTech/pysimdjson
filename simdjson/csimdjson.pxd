# cython: language_level=3
# distutils: language=c++
from libc.stdint cimport uint8_t, uint32_t, uint64_t, int64_t
from libcpp.string cimport string
from cpython cimport PyObject

cdef extern from "util.h":
    cdef void simdjson_error_handler()
    cdef void * flatten_array[T](simd_array src) \
        except +simdjson_error_handler
    cdef void set_active_implementation(Implementation *)
    cdef size_t num_utf8_chars(const char*, size_t)
    cdef object unicode_from_str(const char *, size_t)



cdef extern from "simdjson.h" namespace "simdjson":
    cdef size_t SIMDJSON_MAXSIZE_BYTES
    cdef size_t SIMDJSON_PADDING
    cdef enum:
        SIMDJSON_VERSION_MAJOR
        SIMDJSON_VERSION_MINOR
        SIMDJSON_VERSION_REVISION

    cdef string minify[T](T) except +simdjson_error_handler

    cdef cppclass Implementation "simdjson::implementation":
        const string &name()
        const string &description()
        bint supported_by_runtime_system() const;

    # This is marked as private and internal, but we don't have a choice.
    cdef cppclass AvailableImplementationList \
            "simdjson::internal::available_implementation_list":
        const Implementation * const *begin()
        const Implementation * const *end()

        const Implementation * operator[](string)

    cdef cppclass atomic_ptr[T]:
        pass

    cdef enum error_code "simdjson::error_code":
        SUCCESS = 0,
        CAPACITY,
        MEMALLOC,
        TAPE_ERROR,
        DEPTH_ERROR,
        STRING_ERROR,
        T_ATOM_ERROR,
        F_ATOM_ERROR,
        N_ATOM_ERROR,
        NUMBER_ERROR,
        UTF8_ERROR,
        UNINITIALIZED,
        EMPTY,
        UNESCAPED_CHARS,
        UNCLOSED_STRING,
        UNSUPPORTED_ARCHITECTURE,
        INCORRECT_TYPE,
        NUMBER_OUT_OF_RANGE,
        INDEX_OUT_OF_BOUNDS,
        NO_SUCH_FIELD,
        IO_ERROR,
        INVALID_JSON_POINTER,
        INVALID_URI_FRAGMENT,
        UNEXPECTED_ERROR,
        PARSER_IN_USE,
        OUT_OF_ORDER_ITERATION,
        INSUFFICIENT_PADDING,
        INCOMPLETE_ARRAY_OR_OBJECT,
        SCALAR_DOCUMENT_AS_VALUE,
        OUT_OF_BOUNDS,
        TRAILING_CONTENT,
        NUM_ERROR_CODES

    cdef const char *error_message(error_code)

    cdef cppclass simdjson_result[T]:
        error_code get(T&);

    const AvailableImplementationList& get_available_implementations()
    atomic_ptr["const Implementation"]* get_active_implementation()


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


cdef extern from "simdjson.h" namespace "simdjson::dom":
    cdef cppclass simd_array "simdjson::dom::array":
        cppclass iterator:
            iterator()

            iterator operator++()
            bint operator!=(iterator)
            simd_element operator*()

        simd_array.iterator begin()
        simd_array.iterator end()

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

        simd_object.iterator begin()
        simd_object.iterator end()

        size_t size()

        simd_element at_pointer(const char*) except +simdjson_error_handler
        simd_element operator[](const char*) except +simdjson_error_handler


    cdef cppclass simd_element "simdjson::dom::element":
        element_type type()

        const char *get_c_str()
        size_t get_string_length()

        simd_array get_array()
        simd_object get_object()
        int64_t get_int64()
        uint64_t get_uint64()
        double get_double()
        bint get_bool()

        simd_element at_pointer(const char*) except +simdjson_error_handler


    cdef cppclass simd_document "simdjson::dom::document":
        simd_document() except +
        simd_element root()
        size_t capacity()
        error_code allocate(size_t)


    cdef cppclass simd_parser "simdjson::dom::parser":
        simd_parser() except +simdjson_error_handler
        simd_parser(size_t max_capacity) except +simdjson_error_handler

        simd_element parse(const char *, size_t, bint) \
            except +simdjson_error_handler
        simd_element load(const char *) except +simdjson_error_handler

        simdjson_result[simd_element] parse_into_document(
            simd_document&,
            const uint8_t *,
            size_t,
            bint
        )
