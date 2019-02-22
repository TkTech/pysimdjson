# cython: language_level=2
from json import JSONDecodeError
from pysimdjson cimport CParsedJson, json_parse
from cpython.dict cimport PyDict_SetItem

#: Maximum default depth used when allocating capacity.
cdef int DEFAULT_MAX_DEPTH = 1024


cdef class Iterator:
    cdef CParsedJson.iterator* iter

    def __cinit__(self, ParsedJson pj):
        self.iter = new CParsedJson.iterator(pj.pj)

    def __dealloc__(self):
        del self.iter

    cpdef uint8_t get_type(self):
        return self.iter.get_type()

    cpdef bool isOk(self):
        return self.iter.isOk()

    cpdef bool next(self):
        return self.iter.next()

    cpdef bool down(self):
        return self.iter.down()

    cpdef bool up(self):
        return self.iter.up()

    cpdef double get_double(self):
        return self.iter.get_double()

    cpdef int64_t get_integer(self):
        return self.iter.get_integer()

    cpdef const char * get_string(self):
        return self.iter.get_string()

    def to_obj(self):
        return self._to_obj(self.iter)

    cdef object _to_obj(self, CParsedJson.iterator* iter):
        # This is going to be by far the slowest part of this, as the cost of
        # creating python objects is quite high.
        cdef char t = <char>iter.get_type()
        cdef unicode k
        cdef dict d
        cdef list l

        if t == '[':
            l = []
            if iter.down():
                while True:
                    v = self._to_obj(iter)
                    l.append(v)

                    if not iter.next():
                        break

                iter.up()
            return l
        elif t == '{':
            # Updating the dict is incredibly expensive, consuming the majority
            # of time in most of the JSON tests.
            d = {}
            if iter.down():
                while True:
                    k = iter.get_string().decode('utf-8')
                    iter.next()
                    v = self._to_obj(iter)
                    PyDict_SetItem(d, k, v)

                    if not iter.next():
                        break
                iter.up()
            return d
        elif t == 'd':
            return iter.get_double()
        elif t == 'l':
            return iter.get_integer()
        elif t == '"':
            k = iter.get_string().decode('utf-8')
            return k
        elif t == 't':
            return True
        elif t == 'f':
            return False
        elif t == 'n':
            return None


cdef class ParsedJson:
    """Low-level wrapper for simdjson."""
    cdef CParsedJson pj

    def __init__(self, source=None):
        if source:
            if not self.allocate_capacity(len(source)):
                raise MemoryError

            if not self.parse(source):
                # We have no idea what really went wrong, simdjson oddly just
                # writes to cerr instead of setting any kind of error codes.
                raise JSONDecodeError(
                    'Error parsing document',
                    source.decode('utf-8'),
                    0
                )

    def allocate_capacity(self, size, max_depth=DEFAULT_MAX_DEPTH):
        """Resize the document buffer to `size` bytes."""
        return self.pj.allocateCapacity(size, max_depth)

    def parse(self, source):
        """Parse the given document (as bytes).

            .. note::

                It's up to the caller to ensure that allocate_capacity has been
                called with a sufficiently large size before this method is
                called.

        :param source: The document to be parsed.
        :ptype source: bytes
        :returns: True on success, else False.
        """
        return json_parse(source, len(source), self.pj, True)

    def to_obj(self):
        """Recursively convert a parsed json document to a Python object and
        return it.
        """
        iter = Iterator(self)
        if not iter.isOk():
            # Prooooably not the right exception
            raise JSONDecodeError('Error iterating over document', '', 0)
        return iter.to_obj()

    def items(self, prefix):
        """Similar to the ijson.items() interface, this method allows you to
        extract part of a document without converting the entire document to
        Python objects, which is very expensive.
        """
        cdef list parsed_prefix = parse_prefix(prefix)

        iter = Iterator(self)
        if not iter.isOk():
            raise JSONDecodeError('Error iterating over document', '', 0)

        for key in parsed_prefix:
            if not iter.move_to_key(key):
                return None

        return iter.to_obj()


def loads(s):
    return ParsedJson(s).to_obj()


#: State machine states for parsing item() query strings.
cdef enum:
    Q_UNQUOTED = 10
    Q_QUOTED = 20
    Q_ESCAPE = 30


cpdef list parse_prefix(prefix):
    cdef int current_state = Q_UNQUOTED
    cdef list result = []
    cdef list buff = []

    for c in prefix:
        if current_state == Q_UNQUOTED:
            # Unquoted string
            if c == '"':
                current_state = Q_QUOTED
            elif c == '.':
                if buff:
                    result.append(''.join(buff).encode('utf-8'))
                    del buff[:]
            else:
                buff.append(c)
        elif current_state == Q_QUOTED:
            # Quoted string
            if c == '\\':
                current_state = Q_ESCAPE
            elif c == '"':
                current_state = Q_UNQUOTED
                result.append(''.join(buff).encode('utf-8'))
                del buff[:]
            else:
                buff.append(c)
        elif current_state == Q_ESCAPE:
            # Escape within a quoted string
            buff.append(c)
            current_state = Q_ESCAPE if c == '\\' else Q_QUOTED

    if current_state == Q_QUOTED:
        raise ValueError('Incomplete quoted string')

    if current_state == Q_ESCAPE:
        raise ValueError('Incomplete escape sequence')

    if buff:
        result.append(''.join(buff).encode('utf-8'))

    return result
