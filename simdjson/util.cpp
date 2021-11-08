#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "simdjson.h"
#include "util.h"

/**
 * Error translator, converting simdjson C++ exceptions into sensible Python
 * exceptions.
 *
 * Use it like:
 *
 *      simd_element at(int) except +simdjson_error_handler
 */
void
simdjson_error_handler() {
    using namespace simdjson;

    try {
        if(PyErr_Occurred()) {
            ; // Exception pass-through.
        } else {
            throw;
        }
    } catch (const simdjson_error &e) {
        switch (e.error()) {
            case error_code::NO_SUCH_FIELD:
                PyErr_SetString(PyExc_KeyError, e.what());
                return;
            case error_code::INDEX_OUT_OF_BOUNDS:
                PyErr_SetString(PyExc_IndexError, e.what());
                return;
            case error_code::INCORRECT_TYPE:
                PyErr_SetString(PyExc_TypeError, e.what());
                return;
            case error_code::MEMALLOC:
                PyErr_SetNone(PyExc_MemoryError);
                return;
            case error_code::EMPTY:
            case error_code::STRING_ERROR:
            case error_code::T_ATOM_ERROR:
            case error_code::F_ATOM_ERROR:
            case error_code::N_ATOM_ERROR:
            case error_code::NUMBER_ERROR:
            case error_code::UNESCAPED_CHARS:
            case error_code::UNCLOSED_STRING:
            case error_code::NUMBER_OUT_OF_RANGE:
            case error_code::INVALID_JSON_POINTER:
            case error_code::INVALID_URI_FRAGMENT:
            case error_code::CAPACITY:
            case error_code::TAPE_ERROR:
                PyErr_SetString(PyExc_ValueError, e.what());
                return;
            case error_code::IO_ERROR:
                PyErr_SetString(PyExc_IOError, e.what());
                return;
            case error_code::UTF8_ERROR:
            {
                // simdjson doesn't yet give us any precise details on
                // where the error occured. See upstream#46.
                // PyUnicodeDecodeError_* methods are stubs on PyPy3,
                // so we can't use that helper..
                PyObject *unicode_error = PyObject_CallFunction(
                    PyExc_UnicodeDecodeError,
                    "sy#nns",
                    "utf-8",
                    "",
                    0,
                    0,
                    1,
                    e.what()
                );
                PyErr_SetObject(
                    PyExc_UnicodeDecodeError,
                    unicode_error
                );
                Py_XDECREF(unicode_error);
                return;
            }
            default:
                PyErr_SetString(PyExc_RuntimeError, e.what());
                return;
        }
    }
}
