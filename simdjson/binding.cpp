/**
 * This file provides the low-level bindings around the C++ simdjson library,
 * exposing it to Python as the csimdjson module.
 */
#include <pybind11/pybind11.h>
#include <Python.h>
#include "simdjson.h"

namespace py = pybind11;
using namespace simdjson;

inline py::object element_to_primitive(dom::element e) {
    switch (e.type()) {
    case dom::element_type::OBJECT:
        return py::cast(dom::object(e));
    case dom::element_type::ARRAY:
        return py::cast(dom::array(e));
    case dom::element_type::STRING:
        return py::cast(e.get_string());
    case dom::element_type::INT64:
        return py::cast(e.get_int64());
    case dom::element_type::UINT64:
        return py::cast(e.get_uint64());
    case dom::element_type::DOUBLE:
        return py::cast(e.get_double());
    case dom::element_type::BOOL:
        return py::cast(e.get_bool());
    case dom::element_type::NULL_VALUE:
        return py::none();
    default:
        // This should never, ever, happen. The only way we get here is if
        // simdjson.cpp/.h were updated with new types that don't match JSON
        // types 1:1 and we missed it.
        throw py::value_error(
            "Encountered an unknown element_type."
            " This is an internal pysimdjson error, please report an issue"
            " at https://github.com/TkTech/pysimdjson with the file that"
            " failed."
        );
    }
}

PYBIND11_MAKE_OPAQUE(dom::array);
PYBIND11_MAKE_OPAQUE(dom::object);

PYBIND11_MODULE(csimdjson, m) {
    m.doc() = "Low-level bindings for the simdjson project.";

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

    py::class_<dom::parser>(m, "Parser")
        .def(py::init<>())
        .def(py::init<size_t>(),
                py::arg("max_capacity") = SIMDJSON_MAXSIZE_BYTES)

        .def("load",
            [](dom::parser &self, std::string &path) {
                return element_to_primitive(self.load(path));
            },
            py::return_value_policy::reference_internal
        )
        .def("parse",
            [](dom::parser &self, const std::string &s) {
                return element_to_primitive(self.parse(padded_string(s)));
            },
            py::return_value_policy::reference_internal
        );

    py::class_<dom::array>(m, "Array")
        .def("__truediv__",
            [](dom::array &self, const char *json_pointer) -> py::object {
                return element_to_primitive(self.at(json_pointer));
            },
            py::return_value_policy::reference_internal
        )
        .def("__getitem__",
            [](dom::array &self, int64_t i) -> py::object {
                return element_to_primitive(self.at(i));
            },
            py::return_value_policy::reference_internal
        )
        .def("__len__", [](dom::object &self) { return self.size(); })
        .def("__iter__",
            [](dom::array &self) {
                return py::make_iterator(self.begin(), self.end());
            },
            py::return_value_policy::reference_internal
        );

    py::class_<dom::object>(m, "Object")
        .def("__truediv__",
            [](dom::object &self, const char *json_pointer) -> py::object {
                return element_to_primitive(self.at(json_pointer));
            },
            py::return_value_policy::reference_internal
        )
        .def("at",
            [](dom::object &self, const char *json_pointer) {
                return element_to_primitive(self.at(json_pointer));
            },
            py::return_value_policy::reference_internal,
            "Get the value associated with the given JSON pointer."
        )
        .def("__iter__",
            [](dom::object &self) {
                return py::make_iterator(
                    self.begin(),
                    self.end()
                );
            },
            py::return_value_policy::reference_internal
        )
        .def("__len__", [](dom::object &self) { return self.size(); })
        .def("__getitem__",
            [](dom::object &self, const char *key) -> py::object {
                try {
                    return element_to_primitive(self[key]);
                } catch (const simdjson_error& e) {
                    switch (e.error()) {
                        case error_code::NO_SUCH_FIELD:
                            throw py::key_error("No such key");
                        default:
                            throw;
                    }
                }
            },
            py::return_value_policy::reference_internal
        );
}
