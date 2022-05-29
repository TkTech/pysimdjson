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
#endif
