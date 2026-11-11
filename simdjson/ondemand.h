#ifndef PYSIMDJSON_ONDEMAND_H
#define PYSIMDJSON_ONDEMAND_H

#include <Python.h>
#include <cstring>
#include <memory>
#include "simdjson.h"

namespace pysimdjson {
struct decref {
    void operator()(PyObject *value) const { Py_XDECREF(value); }
};
using pyref = std::unique_ptr<PyObject, decref>;

// Own every Python allocation before another operation can throw a native
// exception. No on-demand value or borrowed string escapes this conversion.
template<class Value>
PyObject *to_python(Value &value, size_t depth = 0) {
    using namespace simdjson;
    using ondemand::json_type;
    if (depth >= DEFAULT_MAX_DEPTH) { throw simdjson_error(DEPTH_ERROR); }
    switch (value.type().value()) {
        case json_type::array: {
            pyref result(PyList_New(0));
            if (!result) { return nullptr; }
            for (auto entry : value.get_array()) {
                auto child = entry.value();
                pyref item(to_python(child, depth + 1));
                if (!item || PyList_Append(result.get(), item.get()) < 0) { return nullptr; }
            }
            return result.release();
        }
        case json_type::object: {
            pyref result(PyDict_New());
            if (!result) { return nullptr; }
            for (auto entry : value.get_object()) {
                auto name = entry.unescaped_key().value();
                pyref key(PyUnicode_DecodeUTF8(name.data(), name.size(), "strict"));
                if (!key) { return nullptr; }
                auto child = entry.value().value();
                pyref item(to_python(child, depth + 1));
                if (!item || PyDict_SetItem(result.get(), key.get(), item.get()) < 0) { return nullptr; }
            }
            return result.release();
        }
        case json_type::string: {
            auto str = value.get_string().value();
            return PyUnicode_DecodeUTF8(str.data(), str.size(), "strict");
        }
        case json_type::number: {
            auto number = value.get_number().value();
            switch (number.get_number_type()) {
                case ondemand::number_type::signed_integer:
                    return PyLong_FromLongLong(number.get_int64());
                case ondemand::number_type::unsigned_integer:
                    return PyLong_FromUnsignedLongLong(number.get_uint64());
                case ondemand::number_type::floating_point_number:
                    return PyFloat_FromDouble(number.get_double());
                default: throw simdjson_error(BIGINT_ERROR);
            }
        }
        case json_type::boolean: return PyBool_FromLong(value.get_bool().value());
        case json_type::null:
            if (!value.is_null().value()) { throw simdjson_error(N_ATOM_ERROR); }
            Py_RETURN_NONE;
        default: throw simdjson_error(TAPE_ERROR);
    }
}

// A stream owns its parser and padded input. Advancing it cannot invalidate any
// yielded Python value. Member order ensures the stream dies before its input.
class records {
    simdjson::padded_string input;
    simdjson::ondemand::parser parser;
    simdjson::ondemand::document_stream stream;
    simdjson::ondemand::document_stream::iterator current;
    size_t batch_size;
    size_t offset{0};
    bool started{false};

    static bool whitespace(char c) {
        return c == ' ' || c == '\t' || c == '\r' || c == '\n';
    }

    bool start_batch() {
        const char *end = input.data() + input.size();
        while (offset < input.size()) {
            const char *begin = input.data() + offset;
            size_t remaining = input.size() - offset;
            // A record of batch_size - 1 bytes can have a two-byte CRLF.
            size_t length = remaining > batch_size ? batch_size + 1 : remaining;
            const char *boundary = begin + length;
            if (boundary < end || length > batch_size) {
                while (boundary > begin && boundary[-1] != '\n') { --boundary; }
                if (boundary == begin) {
                    // Long blank lines need no storage or parsing. Keep their
                    // bytes in input so a later value on the same line still
                    // fails the record-size check.
                    for (size_t i = 0; i < length; ++i) {
                        if (!whitespace(begin[i])) {
                            throw simdjson::simdjson_error(simdjson::CAPACITY);
                        }
                    }
                    offset += length;
                    continue;
                }
            }
            offset = size_t(boundary - input.data());
            // Leave terminators out of the native batch, so its capacity never
            // exceeds batch_size, even for a CRLF split at the read boundary.
            while (boundary > begin && whitespace(boundary[-1])) { --boundary; }
            if (boundary == begin) { continue; }
            if (size_t(boundary - begin) > batch_size) {
                throw simdjson::simdjson_error(simdjson::CAPACITY);
            }
            // Only reset() may consume a BOM, at the start of the input.
            if (boundary - begin >= 3 && std::memcmp(begin, "\xef\xbb\xbf", 3) == 0) {
                throw simdjson::simdjson_error(simdjson::TAPE_ERROR);
            }
            stream = parser.iterate_many(begin, size_t(boundary - begin), batch_size).value();
            current = stream.begin();
            started = true;
            return true;
        }
        return false;
    }
public:
    records(size_t batch_size_, size_t max_capacity)
        : parser(max_capacity), batch_size(batch_size_) {}

    void reset(const char *data, size_t length) {
        stream = simdjson::ondemand::document_stream();
        input = simdjson::padded_string(data, length);
        if (!input.data()) { throw std::bad_alloc(); }
        offset = length >= 3 && std::memcmp(input.data(), "\xef\xbb\xbf", 3) == 0 ? 3 : 0;
        started = false;
    }

    PyObject *next() {
        if (started) { ++current; }
        while (!started || current == stream.end()) {
            if (started && stream.truncated_bytes()) {
                throw simdjson::simdjson_error(simdjson::INCOMPLETE_ARRAY_OR_OBJECT);
            }
            if (!start_batch()) {
                PyErr_SetNone(PyExc_StopIteration);
                return nullptr;
            }
        }
        auto doc = (*current).value();

        // Keep batched parsing, but enforce NDJSON before yielding any part of
        // a line. The native newline-delimited mode assumes valid boundaries
        // and can skip an unread remainder, so it is not a validator.
        auto source = current.source();
        if (std::memchr(source.data(), '\n', source.size())) {
            PyErr_SetString(PyExc_ValueError, "NDJSON records must not span multiple lines");
            return nullptr;
        }
        const char *end = input.data() + input.size();
        const char *line_end = source.data() + source.size();
        for (; line_end < end && *line_end != '\n'; ++line_end) {
            if (*line_end != ' ' && *line_end != '\t' && *line_end != '\r') {
                PyErr_SetString(PyExc_ValueError, "NDJSON requires one JSON value per line");
                return nullptr;
            }
        }
        const char *line_start = source.data();
        while (line_start > input.data() && line_start[-1] != '\n') { --line_start; }
        if (line_start == input.data() && input.size() >= 3 &&
                std::memcmp(line_start, "\xef\xbb\xbf", 3) == 0) {
            line_start += 3;
        }
        if (line_end < end && line_end > line_start && line_end[-1] == '\r') { --line_end; }
        if (size_t(line_end - line_start) >= batch_size) {
            PyErr_SetString(PyExc_ValueError, "NDJSON record must be smaller than batch_size");
            return nullptr;
        }
        return to_python(doc);
    }
};
}
#endif
