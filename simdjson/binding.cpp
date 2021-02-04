/**
 * This file provides the low-level bindings around the C++ simdjson library,
 * exposing it to Python as the csimdjson module.
 */
#define PY_SSIZE_T_CLEAN
#include <vector>
#include <pybind11/pybind11.h>
#include <Python.h>
#include "simdjson.h"

namespace py = pybind11;
using namespace simdjson;

template <typename T>
using VecPtr = std::unique_ptr<std::vector<T>>;

static inline py::object element_to_primitive(dom::element e, bool recursive);

static inline py::object sv_to_unicode(std::string_view sv) {
    /* pybind11 doesn't build in its string_view support if you're
     * targeting c++11, even if string_view is available. So we do it
     * ourselves. */
    PyObject *obj = PyUnicode_FromStringAndSize(sv.data(), sv.size());
    if (!obj) {
        throw py::error_already_set();
    }
    return py::reinterpret_steal<py::object>(obj);
}

static inline py::dict object_to_dict(dom::object obj, bool recursive) {
    py::dict result;

    for (dom::key_value_pair field : obj) {
        auto k = sv_to_unicode(field.key).release().ptr();
        auto v = element_to_primitive(field.value, recursive).release().ptr();
        auto err = PyDict_SetItem(result.ptr(), k, v);
        if (err == -1) throw std::bad_alloc();

        Py_DECREF(k);
        Py_DECREF(v);
    }

    return result;
}

static inline py::list array_to_list(dom::array arr, bool recursive) {
    py::list result(arr.size());
    size_t i = 0;

    for (dom::element field : arr) {
        PyList_SET_ITEM(
            result.ptr(),
            i,
            element_to_primitive(field, recursive).release().ptr()
        );
        i++;
    }

    return result;
}

static inline py::object element_to_primitive(dom::element e, bool recursive = false) {
    switch (e.type()) {
    case dom::element_type::OBJECT:
        if (recursive) return object_to_dict(dom::object(e), recursive);
        return py::cast(dom::object(e));
    case dom::element_type::ARRAY:
        if (recursive) return array_to_list(dom::array(e), recursive);
        return py::cast(dom::array(e));
    case dom::element_type::STRING:
        return sv_to_unicode(e.get_string());
    case dom::element_type::INT64:
        return py::cast(int64_t(e));
    case dom::element_type::UINT64:
        return py::cast(uint64_t(e));
    case dom::element_type::DOUBLE:
        return py::cast(double(e));
    case dom::element_type::BOOL:
        return py::cast(bool(e));
    case dom::element_type::NULL_VALUE:
        return py::none();
    default:
        // This should never, ever, happen. The only way we get here is if
        // simdjson.cpp/.h were updated with new types that don't match JSON
        // types 1:1 and we missed it.
        throw py::value_error(
            "Encountered an unknown element_type.\n"
            "This is an internal pysimdjson error, please report an issue\n"
            "at https://github.com/TkTech/pysimdjson with the file that\n"
            "failed."
        );
    }
}

template <typename T>
static void array_to_vector(dom::array src, VecPtr<T> &dst) {
    for (dom::element field : src) {
        if (field.type() == dom::element_type::ARRAY) {
            array_to_vector(field, dst);
        } else {
            dst->push_back(field);
        }
    }
}

template <typename T>
class ArrayContainer {
    public:
        ArrayContainer(dom::array src)
            : m_vec(VecPtr<T>(new std::vector<T>))
        {
            // This may over-allocate if the array is not flat, since array
            // starts and ends each count as a slot on their own. However,
            // this prevents us from having to grow whenever we find a new
            // child array.
            m_vec->reserve((src.slots() - 1) / 2);

            for (dom::element field : src) {
                if (field.type() == dom::element_type::ARRAY) {
                    array_to_vector<T>(field, m_vec);
                } else {
                    m_vec->push_back(field);
                }
            }

            m_vec->shrink_to_fit();
        }

        VecPtr<T> m_vec;
};

/**
 * This class is used to keep the flat arrays that back exported buffers
 * from `as_buffer()` alive and tied to Python's lifecycles.
 **/
template <typename T>
static void array_container(py::module &m) {
    py::class_<ArrayContainer<T>>(
        m,
        ("ArrayContainer" + py::format_descriptor<T>::format()).c_str(),
        "Internal lifecycle management class for Array buffers.",
        py::buffer_protocol()
    )
    .def_buffer([](ArrayContainer<T> &self) -> py::buffer_info {
        return py::buffer_info(
            self.m_vec->data(),
            sizeof(T),
            py::format_descriptor<T>::format(),
            1,
            { self.m_vec->size() },
            { self.m_vec->size() * sizeof(T) }
        );
    });
}

namespace pybind11 { namespace detail {
    // Caster for the elements in Array.
    template <> struct type_caster<dom::element> {
        public:
            PYBIND11_TYPE_CASTER(dom::element, _("Element"));

            static handle cast(dom::element src, py::return_value_policy, py::handle) {
                return element_to_primitive(src).release();
            }
    };
}}

PYBIND11_MAKE_OPAQUE(dom::array);
PYBIND11_MAKE_OPAQUE(dom::object);

PYBIND11_MODULE(csimdjson, m) {
    m.doc() = "Low-level bindings for the simdjson project.";

    m.attr("MAXSIZE_BYTES") = py::int_(SIMDJSON_MAXSIZE_BYTES);
    m.attr("PADDING") = py::int_(SIMDJSON_PADDING);
    m.attr("DEFAULT_MAX_DEPTH") = py::int_(DEFAULT_MAX_DEPTH);
    m.attr("VERSION") = py::str(STRINGIFY(SIMDJSON_VERSION));

    // We can't just use py::make_iterator & py::make_key_iterator, because
    // simdjson does not implement the expect std::iterator-like and
    // std::pair-like properties. See upstream#1098 for future fixes.
    // It looks tempting to replace with something like ranges-v3, which would
    // turn all of this into a one-liner. However, ranges-v3 requires VS2019
    // which would severely cripple our platform support.
    struct PyKeyIterator {
        PyKeyIterator(
            const dom::object &obj
        ) : obj(obj), first(obj.begin()), end(obj.end()) { }

        py::object next() {
            if (first == end)
                throw py::stop_iteration();

            auto v = first.key();
            first++;
            return sv_to_unicode(v);
        }

        const dom::object &obj;
        dom::object::iterator first;
        dom::object::iterator end;
    };

    struct PyValueIterator {
        PyValueIterator(
            const dom::object &obj
        ) : obj(obj), first(obj.begin()), end(obj.end()) { }

        py::object next() {
            if (first == end)
                throw py::stop_iteration();

            auto v = first.value();
            first++;
            return element_to_primitive(v, true);
        }

        const dom::object &obj;
        dom::object::iterator first;
        dom::object::iterator end;
    };

    struct PyKeyValueIterator {
        PyKeyValueIterator(
            const dom::object &obj
        ) : obj(obj), first(obj.begin()), end(obj.end()) { }

        py::object next() {
            if (first == end)
                throw py::stop_iteration();

            auto v = first.value();
            auto k = first.key();
            first++;
            return py::make_tuple(
                sv_to_unicode(k),
                element_to_primitive(v, true)
            );
        }

        const dom::object &obj;
        dom::object::iterator first;
        dom::object::iterator end;
    };

    array_container<double>(m);
    array_container<int64_t>(m);
    array_container<uint64_t>(m);

    py::class_<PyKeyIterator>(m, "KeyIterator")
        .def("__iter__", [](PyKeyIterator &it) -> PyKeyIterator& { return it; })
        .def("__next__", &PyKeyIterator::next);

    py::class_<PyValueIterator>(m, "ValueIterator")
        .def("__iter__", [](PyValueIterator &it) -> PyValueIterator& { return it; })
        .def("__next__", &PyValueIterator::next);

    py::class_<PyKeyValueIterator>(m, "KeyValueIterator")
        .def("__iter__", [](PyKeyValueIterator &it) -> PyKeyValueIterator& { return it; })
        .def("__next__", &PyKeyValueIterator::next);

    py::register_exception_translator([](std::exception_ptr p) {
        try {
            if (p) std::rethrow_exception(p);
        } catch (const simdjson_error &e) {
            switch (e.error()) {
                case error_code::NO_SUCH_FIELD:
                    throw py::key_error("No such key");
                case error_code::INDEX_OUT_OF_BOUNDS:
                    throw py::index_error("list index out of range");
                case error_code::INCORRECT_TYPE:
                    // We can give better error messages in each class, this is
                    // just a catch-all.
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
                    throw py::value_error(e.what());
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
            throw;
        }
    });

    py::class_<dom::parser>(
            m,
            "Parser",
            "A `Parser` instance is used to load a JSON document.\n"
            "\n"
            "A Parser can be reused to parse multiple documents, in which\n"
            "case it wil reuse its internal buffer, only increasing it if\n"
            "needed.\n"
            "The :class:`~Object` and :class:`~Array` objects returned by\n"
            "a Parser are invalidated when a new document is parsed.\n"
            "\n"
            ":param max_capacity: The maximum size the internal buffer can\n"
            "                     grow to. [default: SIMDJSON_MAXSIZE_BYTES]"
        )
        .def(py::init<>())
        .def(py::init<size_t>(),
                py::arg("max_capacity") = SIMDJSON_MAXSIZE_BYTES)

        .def("load",
            [](dom::parser &self, std::string &path, bool recursive = false) {
                return element_to_primitive(self.load(path), recursive);
            },
            py::arg("path"),
            py::arg("recursive") = false,
            "Load a JSON document from the file system path `path`.\n"
            "\n"
            ":param path: A filesystem path.\n"
            ":param recursive: Recursively turn the document into real\n"
            "                  python objects instead of pysimdjson proxies."
        )
        .def("parse",
            [](dom::parser &self, py::buffer src, bool recursive = false) {
                py::buffer_info info = src.request();

                if (info.format != py::format_descriptor<uint8_t>::format()) {
                    throw py::value_error(
                        "buffer passed to parse() is an invalid format"
                    );
                }

                if (info.ndim != 1) {
                    throw py::value_error(
                        "buffer passed to parse() must be flat."
                    );
                }

                return element_to_primitive(
                    self.parse(
                        padded_string(
                            std::string_view(
                                (const char *)info.ptr,
                                info.itemsize * info.size
                            )
                        )
                    ),
                    recursive
                );
            },
            py::arg("s"),
            py::arg("recursive") = false,
            "Parse a JSON document from the byte string `s`.\n"
            "\n"
            ":param buff: The document to parse.\n"
            ":param recursive: Recursively turn the document into real\n"
            "                  python objects instead of pysimdjson proxies."
        )
        .def_property_static(
            "implementation",
            [](py::object) {
                return py::make_tuple(
                    active_implementation->name(),
                    active_implementation->description()
                );
            },
            [](py::object, std::string name) {
                // Check if it's a valid implementation. simdjson does not
                // check so setting this wrong will segfault on the next
                // parse.
                for (auto implementation : available_implementations) {
                    if (implementation->name() == name) {
                        active_implementation = available_implementations[name];
                        return;
                    }
                }
                throw py::value_error("Unknown implementation");
            }
        )
        .def_property_readonly_static(
            "implementations",
            [](py::object) {
                py::list results;
                for (auto implementation : available_implementations) {
                    results.append(
                        py::make_tuple(
                            implementation->name(),
                            implementation->description()
                        )
                    );
                }
                return results;
            }
        );

    py::class_<dom::array>(
            m,
            "Array",
            "A proxy object that behaves much like a real `list()`.\n"
            "Python objects are not created until an element in the list\n"
            "is accessed.\n\n"
            "Complies with the `collections.abc.Sequence` interface, but\n"
            "does not inherit from it."
        )
        .def("__getitem__",
            [](dom::array &self, int64_t i) {
                // Allow negative indexes which will return counting from the
                // end of the array.
                if (i < 0) i += self.size();
                return element_to_primitive(self.at(i));
            },
            py::return_value_policy::reference_internal
        )
        .def("__getitem__",
            [](dom::array &self, py::slice slice) {
                size_t start, stop, step, slicelength;

                if (!slice.compute(self.size(), &start, &stop, &step, &slicelength))
                    throw py::error_already_set();

                py::list *result = new py::list(slicelength);

                for (size_t i = 0; i < slicelength; ++i) {
                    // py::list doesn't expose the efficient setter for
                    // pre-allocated lists. You CANNOT use PyList_Insert
                    // or you'll segfault.
                    PyList_SET_ITEM(
                        result->ptr(),
                        i,
                        element_to_primitive(self.at(start)).release().ptr()
                    );
                    start += step;
                }

                return result;
            }
        )
        .def("__len__", &dom::array::size)
        .def("__iter__",
            [](dom::array &self) {
                return py::make_iterator(self.begin(), self.end());
            },
            py::return_value_policy::reference_internal,
            py::keep_alive<0, 1>()
        )
        .def("at_pointer",
            [](dom::array &self, const char *json_pointer) {
                return element_to_primitive(self.at_pointer(json_pointer));
            },
            py::return_value_policy::reference_internal,
            "Get the value associated with the given JSON pointer."
        )
        .def("count",
            [](dom::array &self, py::object value) {
                // This is "correct" implementation of count at the cost
                // of performance.
                // We should also make a count for primitive types that
                // converts the `value` just once, and compares against the
                // basic types instead.
                unsigned long long i = 0;
                for (dom::element field : self) {
                    if (element_to_primitive(field).equal(value)) {
                        i++;
                    }
                }
                return i;
            }
        )
        .def("index",
            [](dom::array &self, py::object x, py::object start, py::object end) {
                // Cheat and use py::slice since it takes care of all the edge
                // cases for us.
                auto size = self.size();
                size_t start_i, stop_i, step, slicelength;

                py::slice slice(
                    start.is_none() ? 0 : start.cast<ssize_t>(),
                    end.is_none() ? size : end.cast<ssize_t>(),
                    1
                );

                if (!slice.compute(size, &start_i, &stop_i, &step, &slicelength))
                    throw py::error_already_set();

                for (size_t i = 0; i < slicelength; ++i) {
                    if (element_to_primitive(self.at(start_i)).equal(x)) {
                        return start_i;
                    }
                    start_i += step;
                }

                throw py::value_error();
            },
            py::arg("x"),
            py::arg("start") = py::none(),
            py::arg("end") = py::none()
        )
        .def("as_list",
            [](dom::array &self) {
                return array_to_list(self, true);
            },
            "Convert this Array to a regular python list, recursively\n"
            "converting any objects/lists it finds."
        )
        .def("as_buffer",
            [](dom::array &self, char of_type) {
                switch(of_type) {
                case 'd':
                    return py::cast(ArrayContainer<double>(self));
                case 'i':
                    return py::cast(ArrayContainer<int64_t>(self));
                case 'u':
                    return py::cast(ArrayContainer<uint64_t>(self));
                default:
                    throw py::value_error(
                        "Not a known of_type. Must be one of {d,i,u}."
                    );
                }
            },
            "**Copies** the contents of a **homogeneous** array to an\n"
            "object that can be used as a `buffer`. This means it can be\n"
            "used as input for `numpy.frombuffer`, `bytearray`,\n"
            "`memoryview`, etc. This object has a lifecycle that is\n"
            "independent of the array and the parser.\n"
            "\n"
            "When n-dimensional arrays are encountered, this method will\n"
            "recursively flatten them.\n"
            "\n"
            ":param of_type: One of 'd' (double), 'i' (signed 64-bit\n"
            "                integer) or 'u' (unsigned 64-bit integer).",
            py::kw_only(),
            py::arg("of_type")
        )
        .def_property_readonly("mini",
            [](dom::array &self) -> std::string { return minify(self); },
            "Returns the minified JSON representation of this Array as\n"
            "a `str`."
        )
        .def_property_readonly("slots",
            [](dom::array &self) -> size_t { return self.slots(); },
            "Returns the number of 'slots' consumed by this array.\n"
            "This is not the same thing as `len(array)`, but the number of\n"
            "64bit elements consumed by this Array and all of its children\n"
            "on the simdjson structure tape."
        );

    py::class_<dom::object>(
            m,
            "Object",
            "A proxy object that behaves much like a real `dict()`.\n"
            "Python objects are not created until an element in the Object\n"
            "is accessed.\n\n"
            "Complies with the `collections.abc.Mapping` interface, but\n"
            "does not inherit from it."
        )
        .def("__len__", &dom::object::size)
        .def("__getitem__",
            [](dom::object &self, const char *key) {
                return element_to_primitive(self[key]);
            },
            py::return_value_policy::reference_internal
        )
        .def("__contains__",
            [](dom::object &self, const char *key) {
                simdjson_result<dom::element> result = self[key];
                return result.error() ? false : true;
            }
        )
        .def("__iter__",
            [](dom::object &self) { return PyKeyIterator(self); },
            py::return_value_policy::reference_internal,
            py::keep_alive<0, 1>()
        )
        .def("at_pointer",
            [](dom::object &self, const char *json_pointer) {
                return element_to_primitive(self.at_pointer(json_pointer));
            },
            py::return_value_policy::reference_internal,
            "Get the value associated with the given JSON pointer."
        )
        .def("get",
            [](dom::object &self, const char *key, py::object def) {
                try {
                    return element_to_primitive(self[key]);
                } catch (const simdjson_error &e) {
                    if (e.error() == error_code::NO_SUCH_FIELD) {
                        return def;
                    }
                    throw;
                }
            },
            py::arg("key"),
            py::arg("default") = py::none(),
            py::return_value_policy::reference_internal,
            "Return the value of `key`, or `default` if the key does\n"
            "not exist."
        )
        .def("keys",
            [](dom::object &self) { return PyKeyIterator(self); },
            "Returns an iterator over all keys in this `Object`."
        )
        .def("values",
            [](dom::object &self) { return PyValueIterator(self); },
            "Returns an iterator over of all values in this `Object`."
        )
        .def("items",
            [](dom::object &self) { return PyKeyValueIterator(self); },
            py::return_value_policy::reference_internal,
            py::keep_alive<0, 1>(),
            "Returns an iterator over all the (key, value) pairs in this\n"
            "`Object`."
        )
        .def("as_dict",
            [](dom::object &self) {
                return object_to_dict(self, true);
            },
            "Convert this `Object` to a regular python dictionary,\n"
            "recursively converting any objects or lists it finds."
        )
        .def_property_readonly("mini",
            [](dom::object &self) -> std::string { return minify(self); },
            "Returns the minified JSON representation of this Object as\n"
            "a `str`."
        );
}
