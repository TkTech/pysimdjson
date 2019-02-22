# cython: language_level=2
from json import JSONDecodeError
from pysimdjson cimport CParsedJson, json_parse

cdef int DEFAULT_MAX_DEPTH = 1024


cdef class ParsedJson:
    """Low-level wrapper for simdjson."""
    cdef CParsedJson pj

    def __init__(self, source=None):
        if source:
            if not self.allocate_capacity(len(source)):
                raise MemoryError

            if not self.parse(source):
                raise JSONDecodeError

    def allocate_capacity(self, size, max_depth=DEFAULT_MAX_DEPTH):
        return self.pj.allocateCapacity(size, max_depth)

    def parse(self, source):
        return json_parse(source, len(source), self.pj, True)

    def to_obj(self):
        iter = new CParsedJson.iterator(self.pj)
        try:
            if not iter.isOk():
                # Prooooably not the right exception
                raise JSONDecodeError
            return self._to_obj(iter)
        finally:
            del iter

    cdef object _to_obj(self, CParsedJson.iterator *iter):
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
                    d[k] = v

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


def loads(s):
    return ParsedJson(s).to_obj()
