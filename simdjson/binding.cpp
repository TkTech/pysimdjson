/**
 * This file provides the low-level bindings around the C++ simdjson library,
 * exposing it to Python as the csimdjson module.
 *
 * For the most part, it's a direct 1:1 binding with the API found in simdjson.
 */
#include <pybind11/pybind11.h>
#include <Python.h>
#include "simdjson.h"

namespace py = pybind11;
using namespace simdjson;

#if defined(__GNUC__) || defined(__INTEL_COMPILER)
#define PY_LIKELY(x) __builtin_expect(!!(x), 1)
#define PY_UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#define PY_LIKELY(x) (x)
#define PY_UNLIKELY(x) (x)
#endif

/**
 * Utility to convert std::string_view to a decoded Python string.
 *
 * Since simdjson already did UTF-8 validation, this method will convert while
 * ignoring any UTF-8 codec errors from CPython.
 */
inline PyObject* string_view_to_str(const std::string_view s) {
    return PyUnicode_DecodeUTF8(s.data(), s.size(), "ignore\0");
}

/** 
 * Converts a simdjson dom::element to a high-level Python object.
 *
 * When converting arrays or objects, it will recursively convert all children
 * as well.
 */
PyObject* element_to_primitive(const dom::element &e) {
    switch (e.type()) {
    case dom::element_type::ARRAY:
        {
            dom::array arr = e.get_array();
            auto size = arr.size();
            auto i = 0;

            PyObject *result = PyList_New(size);

            for (dom::element array_element : arr) {
                PyList_SET_ITEM(result, i, element_to_primitive(array_element));
                i++;
            }

            return result;
        }
    case dom::element_type::OBJECT:
        {
			dom::object obj = e.get_object();

            PyObject *result = PyDict_New();

            for (dom::key_value_pair field : obj) {
                auto key = string_view_to_str(field.key);
                auto value = element_to_primitive(field.value);

                PyDict_SetItem(result, key, value);

                Py_DECREF(key);
                Py_DECREF(value);
            }

            return result;
        }
    case dom::element_type::INT64:
        return PyLong_FromLongLong(e.get_int64());
    case dom::element_type::UINT64:
		return PyLong_FromUnsignedLongLong(e.get_uint64());
    case dom::element_type::DOUBLE:
		return PyFloat_FromDouble(e.get_double());
    case dom::element_type::STRING:
		return string_view_to_str(e.get_string());
    case dom::element_type::BOOL:
		if (e.get_bool()) {
			Py_RETURN_TRUE;
		} else {
			Py_RETURN_FALSE;
		}
    case dom::element_type::NULL_VALUE:
    default:
        Py_RETURN_NONE;
    }
}

PYBIND11_MODULE(csimdjson, m) {
    m.doc() = 
        "Low-level bindings for the simdjson project.\n\n"
        "Typically, you won't use this module directly, but would"
        " import the simdjson module instead, which acts more like"
        " python's built-in json module.";

    m.attr("MAXSIZE_BYTES") = py::int_(SIMDJSON_MAXSIZE_BYTES);
    m.attr("PADDING") = py::int_(SIMDJSON_PADDING);
    m.attr("DEFAULT_MAX_DEPTH") = py::int_(DEFAULT_MAX_DEPTH);

    py::enum_<error_code>(m, "error_code", py::arithmetic())
        .value("SUCCESS", error_code::SUCCESS)
        .value("CAPACITY", error_code::CAPACITY)
        .value("MEMALLOC", error_code::MEMALLOC)
        .value("TAPE_ERROR", error_code::TAPE_ERROR)
        .value("DEPTH_ERROR", error_code::DEPTH_ERROR)
        .value("STRING_ERROR", error_code::STRING_ERROR)
        .value("T_ATOM_ERROR", error_code::T_ATOM_ERROR)
        .value("F_ATOM_ERROR", error_code::F_ATOM_ERROR)
        .value("N_ATOM_ERROR", error_code::N_ATOM_ERROR)
        .value("NUMBER_ERROR", error_code::NUMBER_ERROR)
        .value("UTF8_ERROR", error_code::UTF8_ERROR)
        .value("UNINITIALIZED", error_code::UNINITIALIZED)
        .value("EMPTY", error_code::EMPTY)
        .value("UNESCAPED_CHARS", error_code::UNESCAPED_CHARS)
        .value("UNCLOSED_STRING", error_code::UNCLOSED_STRING)
        .value("UNSUPPORTED_ARCHITECTURE", error_code::UNSUPPORTED_ARCHITECTURE)
        .value("INCORRECT_TYPE", error_code::INCORRECT_TYPE)
        .value("NUMBER_OUT_OF_RANGE", error_code::NUMBER_OUT_OF_RANGE)
        .value("INDEX_OUT_OF_BOUNDS", error_code::INDEX_OUT_OF_BOUNDS)
        .value("NO_SUCH_FIELD", error_code::NO_SUCH_FIELD)
        .value("IO_ERROR", error_code::IO_ERROR)
        .value("INVALID_JSON_POINTER", error_code::INVALID_JSON_POINTER)
        .value("INVALID_URI_FRAGMENT", error_code::INVALID_URI_FRAGMENT)
        .value("UNEXPECTED_ERROR", error_code::UNEXPECTED_ERROR);

    py::enum_<dom::element_type>(m, "element_type", py::arithmetic())
        .value("ARRAY", dom::element_type::ARRAY)
        .value("OBJECT", dom::element_type::OBJECT)
        .value("INT64", dom::element_type::INT64)
        .value("UINT64", dom::element_type::UINT64)
        .value("DOUBLE", dom::element_type::DOUBLE)
        .value("STRING", dom::element_type::STRING)
        .value("BOOL", dom::element_type::BOOL)
        .value("NULL_VALUE", dom::element_type::NULL_VALUE);


    // Base class for all errors except for MEMALLOC (which becomes a
    // MemoryError subclass) and IO_ERROR (which becomes an IOError subclass).
    static py::exception<simdjson_error> ex_simdjson_error(m,
            "SimdjsonError", PyExc_RuntimeError);
    static py::exception<simdjson_error> ex_capacity(m,
            "CapacityError", ex_simdjson_error.ptr());
    static py::exception<simdjson_error> ex_memalloc(m,
            "MemallocError", PyExc_MemoryError);
    static py::exception<simdjson_error> ex_no_such_field(m,
            "NoSuchFieldError", ex_simdjson_error.ptr());
    static py::exception<simdjson_error> ex_index_out_of_bounds(m,
            "IndexOutOfBoundsError", ex_simdjson_error.ptr());
    static py::exception<simdjson_error> ex_incorrect_type(m,
            "IncorrectTypeError", ex_simdjson_error.ptr());
    static py::exception<simdjson_error> ex_invalid_json_pointer(m,
            "InvalidJSONPointerError", ex_simdjson_error.ptr());

    py::register_exception_translator([](std::exception_ptr p) {
        /* Converts simdjson_error exceptions into higher-level Python
         * exceptions for a more typical Python experience.
         * */
        try {
            if (p) std::rethrow_exception(p);
        } catch (const simdjson_error &e) {
            switch (e.error()) {
                case error_code::NO_SUCH_FIELD:
                    ex_no_such_field(e.what());
                    break;
                case error_code::INDEX_OUT_OF_BOUNDS:
                    ex_index_out_of_bounds(e.what());
                    break;
                case error_code::INCORRECT_TYPE:
                    ex_incorrect_type(e.what());
                    break;
                case error_code::INVALID_JSON_POINTER:
                    ex_invalid_json_pointer(e.what());
                    break;
                case error_code::CAPACITY:
                    ex_capacity(e.what());
                    break;
                case error_code::MEMALLOC:
                    ex_memalloc(e.what());
                    break;
                default:
                    ex_simdjson_error(e.what());
            }
        }
    });

    py::class_<dom::parser>(m, "parser")
        .def(py::init<>())
        .def(py::init<size_t>(),
                py::arg("max_capacity") = SIMDJSON_MAXSIZE_BYTES)

        .def("load",
            [](dom::parser &p, std::string &path) {
                return p.load(path).value();
            },
            py::return_value_policy::take_ownership,
            py::keep_alive<0, 1>()
        )

        .def("parse",
            [](dom::parser &p, const std::string &s) {
                return p.parse(padded_string(s)).value();
            },
            py::return_value_policy::take_ownership,
            py::keep_alive<0, 1>()
        );

    py::class_<dom::element>(m, "element")
        .def_property_readonly("type", &dom::element::type)
        .def("at",
            [](dom::element &e, const char *json_pointer) {
                return e.at(json_pointer).value();
            },
            py::return_value_policy::take_ownership,
            "Get the value associated with the given JSON pointer."
        )
        .def("__getitem__",
            [](dom::element &e, const char *key) {
                try {
                    return e[key].value();
                } catch (const simdjson_error& e) {
                    switch (e.error()) {
                        case error_code::NO_SUCH_FIELD:
                            throw py::key_error("No such key");
                        default:
                            throw;
                    }
                }
            },
            py::return_value_policy::take_ownership
        )
        .def("__truediv__",
            [](dom::element &e, const char *json_pointer) {
                return e.at(json_pointer).value();
            },
            py::return_value_policy::take_ownership
        )
        .def_property_readonly(
            "up",
            [](dom::element &e) {
                // return static_cast<py::handle>(element_to_primitive(e));
                return py::reinterpret_steal<py::object>(element_to_primitive(e));
            },
            py::return_value_policy::move,
            "Uplift a simdjson element to a primitive Python type."
        );
}
