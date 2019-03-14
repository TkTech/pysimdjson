# cython: language_level=2
from libc.stdint cimport int8_t, uint8_t, int64_t, uint64_t, uint32_t
from libcpp cimport bool

cdef extern from 'src/simdjson.h':
    cdef cppclass CParsedJson 'ParsedJson':
        ParsedJson() except +

        cppclass iterator:
            iterator(CParsedJson&)

            bool isOk()
            inline bool prev()
            inline bool next()
            inline bool down()
            inline bool up()
            bool move_forward()
            void to_start_scope()

            uint8_t get_type()
            size_t get_tape_location()
            size_t get_tape_length()
            size_t get_depth()
            size_t get_scope_type()

            bool is_object_or_array()
            bool is_object()
            bool is_array()
            bool is_string()
            bool is_integer()
            bool is_double()

            inline double get_double()
            inline int64_t get_integer()
            const char * get_string()
            uint32_t get_string_length()

        bool allocateCapacity(size_t, size_t)
        bool isValid()

        uint64_t * tape
        uint8_t * string_buf
        uint32_t n_structural_indexes;
        uint32_t *structural_indexes;

    int json_parse(
        const char *,
        size_t len,
        CParsedJson&,
        bool
    )

# Do not remove this, we're tricking Cython into importing the .cpp here. I
# imagine at some point the cpp will be removed entirely as the amalgamation
# script improves and we'll just have the header.
cdef extern from 'src/simdjson.cpp':
    pass


cdef extern from 'cpuid.c':
    int8_t can_use_avx2()
