#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "simdjson.h"

#ifndef _PY_SIMDJSON_ERRORS
#define _PY_SIMDJSON_ERRORS
    void simdjson_error_handler();
    template<typename T>
    void * flatten_array(simdjson::dom::array src, size_t *size);

    template<typename T>
    void _flatten_array(T ** buffer, simdjson::dom::array src) {
        for (simdjson::dom::element field : src) {
            if (field.type() == simdjson::dom::element_type::ARRAY) {
                _flatten_array<T>(buffer, field);
            } else {
                **buffer = (T)field;
                (*buffer)++;
            }
        }
    }

    template<typename T>
    void * flatten_array(simdjson::dom::array src, size_t *size) {
        // This will over-allocate if the array is not flat, since array starts
        // and ends each count as a slot on their own. However, this prevents
        // us from having to grow whenever we find a new child array.
        T * data = (T*)PyMem_Malloc(sizeof(T) * (src.number_of_slots() / 2));
        T * start = data;
        if (!data) return NULL;

        try {
            _flatten_array<T>(&start, src);
        } catch(...) {
            PyMem_Free(data);
            throw;
        }

        *size = (char*)start - (char*)data;
        // TODO: Realloc if too large
        return (void*)data;
    }

    // This exists as a workaround to Cython 0.29 apparently not supporting
    // overloading "atomic_ptr& operator=(T*)" on atomic_ptr, meaning we
    // can't assign an implementation to the pointer. I'm probably just
    // using it wrong :)
    inline void set_active_implementation(const simdjson::implementation *t) {
        simdjson::get_active_implementation() = t;
        return;
    }

    inline size_t num_utf8_chars(const char *src, size_t len) {
        size_t count = 0;
        for (size_t i = 0; i < len; i++) {
            if (simdjson_likely(src[i] >> 6 != 2)) {
                count++;
            }
        }
        return count;
    }

    inline PyObject *unicode_from_str(const char *src, size_t len) {
        size_t num_chars = num_utf8_chars(src, len);

        // Exploit the internals of CPython's unicode implementation to
        // implement a fast-path for ASCII data, which is by far the
        // most common case. This is the single greatest performance gain
        // of any optimization in this library.
        if (simdjson_likely(num_chars == len)) {
            PyObject *uni = PyUnicode_New(len, 127);
            if (!uni) return NULL;
            PyASCIIObject *uni_ascii = (PyASCIIObject*)uni;
            memcpy(uni_ascii + 1, src, len);
            return uni;
        }

        return PyUnicode_DecodeUTF8(src, len, NULL);
    }
#endif
