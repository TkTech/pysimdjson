from json import JSONDecodeError
from libc.string cimport strcmp

cimport cython
from csimdjson cimport CParsedJson, json_parse, can_use_avx2

# Maximum default depth used when allocating capacity.
cdef int DEFAULT_MAX_DEPTH = 1024

cdef long JSON_VALUE_MASK = 0xFFFFFFFFFFFFFF

# State machine states for parsing item() query strings.
cdef enum:
    # Parsing an unquoted string.
    Q_UNQUOTED = 10
    # Parsing a quoted string
    Q_QUOTED = 20
    # Parsing an escape sequence
    Q_ESCAPE = 30

    # No particular operation, default state.
    N_NONE = 0
    # 'GET' (the . operator)
    N_GET = 10
    # [] operator
    N_ARRAY = 20
    # [<N>] operator
    N_ARRAY_SINGLE = 30
    # [<N>:<N>] operator
    N_ARRAY_SLICE = 40


cdef enum ErrorCodes:
    SUCCESS = 0
    CAPACITY = 1
    MEMALLOC = 2
    TAPE_ERROR = 3


cdef unicode _error_msg(int error_code):
    # Stick to if/elif, Cython will translate this into an efficient switch()
    # since it knows the type of error_code.
    if error_code == ErrorCodes.SUCCESS:
        return u'No errors'
    elif error_code == ErrorCodes.CAPACITY:
        return (
            u'Buffer is smaller than document, call allocate_capacity'
            u' to increase the size of the buffer.'
        )
    elif error_code == ErrorCodes.MEMALLOC:
        return u'Error occured while allocating memory.'
    elif error_code == ErrorCodes.TAPE_ERROR:
        return u'Erorr occured while writing to the tape.'
    else:
        return u'Unknown error occured.'


cdef object _to_obj(CParsedJson.iterator* iter):
    # This is going to be by far the slowest part of this, as the cost of
    # creating python objects is quite high.
    # TODO: We can do better. The recursive method might be simple, but the
    # overhead of calling this 13 million times while processing sandiego.json
    # can't be ignored.
    cdef char t = <char>iter.get_type()
    cdef unicode k
    cdef dict d
    cdef list l

    if t == '[':
        l = []
        if iter.down():
            while True:
                v = _to_obj(iter)
                l.append(v)

                if not iter.next():
                    break

            iter.up()
        return l
    elif t == '{':
        d = {}
        if iter.down():
            while True:
                k = iter.get_string()[:iter.get_string_length()].decode('utf-8')
                iter.next()
                d[k] = _to_obj(iter)

                if not iter.next():
                    break
            iter.up()
        return d
    elif t == 'd':
        return iter.get_double()
    elif t == 'l':
        return iter.get_integer()
    elif t == '"':
        k = iter.get_string()[:iter.get_string_length()].decode('utf-8')
        return k
    elif t == 't':
        return True
    elif t == 'f':
        return False
    elif t == 'n':
        return None


cdef class Iterator:
    """A wrapper around the interal simdjson ParsedJson::iterator
    object.

    Typically, it's only useful to use this object if you have very specific
    needs, such as handling JSON with duplicate keys.

        .. note::

            This is a _very_ thin wrapper around the underlying simdjson
            structures. This means that it is possible for this interface to
            change between versions. If you depend on this, you should pin the
            version of simdjson you are using until you can confirm that the
            update works (which is just good practice in general!).

            High-level interfaces like :func:`~loads()` and
            :func:`~ParsedJson.items()` are reliable and will always be
            available.

    """
    cdef CParsedJson.iterator* iter

    def __cinit__(self, ParsedJson pj):
        self.iter = new CParsedJson.iterator(pj.pj)

    def __dealloc__(self):
        del self.iter

    cpdef bool isOk(self):
        """True if the internal state of the iterator is valid."""
        return self.iter.isOk()

    cpdef bool prev(self):
        """Move to the previous element in the document. This will return False
        if already at the start of the current scope."""
        return self.iter.prev()

    cpdef bool next(self):
        """Move to the next element in the document. This will return False if
        the end of the current scope has been reached."""
        return self.iter.next()

    cpdef bool down(self):
        """Enter the current scope and move down a level in the document."""
        return self.iter.down()

    cpdef bool up(self):
        """Exit the current scope and move up a level in the document."""
        return self.iter.up()

    cpdef bool move_forward(self):
        """Move forward along the tape in document order. This will enter and
        exit scopes automatically, so it can be used to traverse an entire
        document.
        """
        return self.iter.move_forward()

    cpdef void to_start_scope(self):
        """Move to the start of the current scope."""
        self.iter.to_start_scope()
        return

    cpdef uint8_t get_type(self):
        """The type of the current element the iterator is pointing to. This
        can be one of `"{}[]tfnrl`."""
        return self.iter.get_type()

    cpdef size_t get_tape_location(self):
        """The iterator's current location within the underlying tape
        structure."""
        return self.iter.get_tape_location()

    cpdef size_t get_tape_length(self):
        """The total length of the underlying tape structure.

        The length of the tape is _not_ the same as the # of elements in the
        document. Some elements consume more than a single entry on the tape.
        """
        return self.iter.get_tape_length()

    cpdef size_t get_depth(self):
        """The current depth of the iterator in the tree."""
        return self.iter.get_depth()

    cpdef size_t get_scope_type(self):
        """Like :func:`~Iterator.get_type()`, except it returns the type of the
        containing scope. For example, given a state like this:

            .. code-block:: json

                {
                    "hello": "world"
                }

            ... and the iterator is currently on "world", this method would
            return `{`, as it is contained within an object/dict.
        """
        return self.iter.get_scope_type()

    cpdef bool is_object_or_array(self):
        """True if the current element is an object/dict or an array (elements
        for which :func:`~Iterator.get_type()` return either `{` or `[`)"""
        return self.iter.is_object_or_array()

    cpdef bool is_object(self):
        """True if the current element is an object/dict."""
        return self.iter.is_object()

    cpdef bool is_array(self):
        """True if the current element is an array."""
        return self.iter.is_array()

    cpdef bool is_string(self):
        """True if the current element is a string."""
        return self.iter.is_string()

    cpdef bool is_integer(self):
        """True if the current element is an integer."""
        return self.iter.is_integer()

    cpdef bool is_double(self):
        """True if the current element is a double."""
        return self.iter.is_double()

    cpdef double get_double(self):
        """Return the current element as a double. This is only valid if
        :func:`~Iterator.is_double()` is True."""
        return self.iter.get_double()

    cpdef int64_t get_integer(self):
        """Return the current element as an integer. This is only valid if
        :func:`~Iterator.is_integer()` is True."""
        return self.iter.get_integer()

    cpdef bytes get_string(self):
        """Return the current element as byte string. This is only valid if
        :func:`~Iterator.is_string()` is True.

            .. note::

                Internally, all the strings are encoded UTF-8. To use this byte
                string in Python as unicode call `get_string().decode('utf-8')`.
        """
        return <bytes>self.iter.get_string()[:self.iter.get_string_length()]

    def to_obj(self):
        """Convert the current iterator and all of its children into Python
        objects and return them."""
        return _to_obj(self.iter)


cdef class ParsedJson:
    """Low-level wrapper for simdjson.

    Providing a `source` document is a shortcut for calling
    :func:`~ParsedJson.allocate_capacity()` and :func:`~ParsedJson.parse()`.
    """
    cdef CParsedJson pj


    def __init__(self, source=None):
        avx2 = can_use_avx2()
        if avx2 == -1:
            raise RuntimeError(
                'simdjson requires AVX2 support, however it has not been'
                ' enabled by your operating system.'
            )
        elif avx2 == 0:
            raise RuntimeError(
                'simdjson requires AVX2 support, which is not provided by'
                ' your processor.'
            )


        if source:
            if not self.allocate_capacity(len(source)):
                raise MemoryError

            self.parse(source)

    def allocate_capacity(self, size, max_depth=DEFAULT_MAX_DEPTH):
        """Resize the document buffer to `size` bytes."""
        return self.pj.allocateCapacity(size, max_depth)

    def parse(self, source):
        """Parse the given document (as bytes).

            .. note::

                It's up to the caller to ensure that allocate_capacity has been
                called with a sufficiently large size before this method is
                called.
        """
        cdef int parse_result = json_parse(source, len(source), self.pj, True)

        if parse_result != 0:
            if parse_result == ErrorCodes.MEMALLOC:
                raise MemoryError

            raise JSONDecodeError(
                _error_msg(parse_result),
                source.decode('utf-8'),
                0
            )

        return self.is_valid()

    def to_obj(self):
        """Recursively convert a parsed json document to a Python object and
        return it.
        """
        cdef Iterator iter = Iterator(self)

        if not iter.isOk():
            # Prooooably not the right exception
            raise JSONDecodeError('Error iterating over document', '', 0)

        return iter.to_obj()

    @property
    def _tape(self):
        cdef:
            uint64_t[:] tape
            uint64_t root
            uint64_t tape_type

        if self.pj.isValid():
            # If the ParsedJson is valid we look at the payload of the first
            # node which contains the total length of the tape. We need to know
            # the length to create an efficient memoryview over it.
            root = self.pj.tape[0]
            tape_type = root >> 56
            if not tape_type == 'r':
                # Iterator.get_tape_length does the same check, but is this
                # case even possible?
                return

            tape = <uint64_t[:root & JSON_VALUE_MASK]>self.pj.tape
            return tape

    def items(self, query):
        """Given a `query` string, find matching elements in the document and
        return them.

        If you only desire part of a document, this method offers significant
        oppertunities for performance gains, as it will avoid creating Python
        objects for anything other than the matching objects. For example, if
        you have a situation where you check a boolean, such as:

            .. code-block:: json

                {"results": ["...50MB..."], "success": true}

        ... you could check just the success field before wasting time loading
        the entire document into Python objects.

            .. code-block:: python

                with open("myjson.json", "rb") as source:
                    pj = ParsedJson(source)
                    if pj.items(".success"):
                        document = pj.to_obj()

            .. note::

                It's important to note this is not using iterative parsing. By
                the time `items()` can be used, the entire document has already
                been parsed (which is relatively fast), but has not been
                converted into Python objects (which is relatively slow).
        """
        cdef list parsed_query = parse_query(query)

        iter = Iterator(self)
        if not iter.isOk():
            raise JSONDecodeError('Error iterating over document', '', 0)

        return self._items(iter, parsed_query)

    cpdef bool is_valid(self):
        """True if the internal state of the parsed json is valid."""
        return self.pj.isValid()

    cdef object _items(self, Iterator iter, list parsed_query):
        # TODO: Proof-of-concept, needs an optimization pass.
        if not parsed_query:
            return

        cdef:
            char t = <char>iter.get_type()
            int op
            int current_index = 0
            int segments
            object obj = None
            list array_result

        op, v = parsed_query[0]
        segments = len(parsed_query)

        if op == N_GET:
            if t == '{':
                # We're getting the entire object, no further filtering
                # required.
                if v == b'':
                    if segments > 1:
                        # There are more query fragments, so we have
                        # further filtering to do...
                        obj = self._items(iter, parsed_query[1:])
                    else:
                        # ... otherwise, we want the entire result.
                        obj = iter.to_obj()
                    return obj

                # We're looking for a specific field.
                if iter.down():
                    while True:
                        if v == b'' or v == iter.get_string():
                            # Found a matching key, move to the value.
                            iter.next()
                            if segments > 1:
                                # There are more query fragments, so we have
                                # further filtering to do...
                                obj = self._items(iter, parsed_query[1:])
                            else:
                                # ... otherwise, we want the entire result.
                                obj = iter.to_obj()
                            break
                        else:
                            # Didn't find a match, skip over the value and move
                            # to the next key.
                            iter.next()

                        if not iter.next():
                            break

                    iter.up()
                return obj
        elif op == N_ARRAY:
            # We're fetching an entire array.
            array_result = []

            if iter.down():
                while True:
                    if segments > 1:
                        array_result.append(
                            self._items(
                                iter,
                                parsed_query[1:]
                            )
                        )
                    else:
                        array_result.append(iter.to_obj())

                    if not iter.next():
                        break

                    current_index += 1

                iter.up()
            return array_result
        elif op == N_ARRAY_SINGLE:
            # We're fetchign a single element from an array.
            # Returns None rather than the possibly-expected IndexError if the
            # index requested doesn't exist in the list. This matches jq
            # behaviour.
            stop_index = int(v[0])
            if iter.down():
                while True:
                    if not current_index == stop_index:
                        current_index += 1

                        if not iter.next():
                            break

                        continue

                    if segments > 1:
                        obj = self._items(iter, parsed_query[1:])
                    else:
                        obj = iter.to_obj()

                    break

                iter.up()
            return obj
        elif op == N_ARRAY_SLICE:
            # We're fetching an arbitrary slice from an array.
            start_index = 0 if not v[0] else int(v[0])
            stop_index = None if not v[1] else int(v[1])

            array_result = []

            if iter.down():
                # Skip ahead to the first starting element. I believe we may be
                # able to get this up to constant time by exposing a bit more
                # of the tape from the simdjson as long as we know the position
                # where the current scope ends.
                while current_index < start_index:
                    if not iter.next():
                        # We got to the end of the list and still didn't find
                        # the starting point.
                        iter.up()
                        return array_result
                    current_index += 1

                while True:
                    if stop_index is not None:
                        if stop_index == current_index:
                            break

                    if segments > 1:
                        array_result.append(self._items(iter, parsed_query[1:]))
                    else:
                        array_result.append(iter.to_obj())

                    if not iter.next():
                        break

                    current_index += 1

                iter.up()
            return array_result


def loads(s):
    """
    Deserialize and return the entire JSON object in `s` (bytes).

    .. note::

        Unlike the built-in Python `json.loads`, this method only
        accepts byte strings, as simdjson will only work on encoded UTF-8.
    """
    return ParsedJson(s).to_obj()



cpdef list parse_query(query):
    """Parse a query string for use with :func:`~ParsedJson.items`.

    Returns a list in the form of `[(<op>, <value>), ...]`.

        .. note::

            This is exposed to Python solely for testing. A typical application
            will never need to call this method.


    This method is...interesting. It decomposes a sorta-jq query string into
    a list of actions. For example, given the query `.results[].valid` it will
    be decomposed into:

        .. code-block:: python

            [
                [Q_GET, "results"],
                [Q_ARRAY, ""],
                [Q_GET, "valid"]
            ]

    If you need to use a field name that contains `[` or `.`, just quote it.
    `."res[]\"lts"` would be perfectly valid.
    """
    cdef int current_state = Q_UNQUOTED
    cdef int current_op = N_NONE

    cdef list result = []

    # A reference to the encoded string *must* be retained or we'll segfault
    # when accessing c_query.
    query = query.encode('utf-8')
    cdef char* c_query = query
    cdef char c
    cdef bytearray buff = bytearray()

    for c in c_query:
        if current_state == Q_UNQUOTED:
            # A regular character without any particular state.
            if c == '.':
                # Starting an object "get"
                if current_op:
                    result.append((
                        current_op,
                        bytes(buff)
                    ))
                    del buff[:]

                current_op = N_GET
            elif c == '[':
                # Starting a new array subscript.
                if current_op:
                    result.append((
                        current_op,
                        bytes(buff)
                    ))
                    del buff[:]

                current_op = N_ARRAY
            elif c == ']':
                # Ending an array subscript.
                if current_op != N_ARRAY:
                    raise ValueError('Stray ] in query string.')

                if buff:
                    # A bit messy, but we want to be able to [eventually]
                    # provide better error messages on bad query strings, so we
                    # need to actually go over everything rather than just
                    # .split().
                    current_op = N_ARRAY_SINGLE
                    slice_parts = []
                    current_slice = bytearray()
                    for c in bytes(buff):
                        if c >= 48 and c <= 57:
                            # Simple nubmer
                            current_slice.append(c)
                        elif c == 58:
                            # Slice delimiter [:]
                            slice_parts.append(bytes(current_slice))
                            current_op = N_ARRAY_SLICE
                        else:
                            raise ValueError(
                                'Do not know how to handle {0!r} in '
                                'array subscript'.format(
                                    chr(c)
                                )
                            )

                    if current_slice:
                        slice_parts.append(bytes(current_slice))

                    result.append((
                        current_op,
                        slice_parts
                    ))
                else:
                    result.append((
                        current_op,
                        None
                    ))

                del buff[:]
                current_op = N_NONE
            elif c == '"':
                # Start of a quoted string.
                current_state = Q_QUOTED
            else:
                # Regular character with no special meaning.
                buff.append(c)
        elif current_state == Q_QUOTED:
            # Contents of a quoted string.
            if c == '\\':
                # Found the start of an escape sequence.
                current_state = Q_ESCAPE
            elif c == '"':
                # Found the end of a quoted string.
                current_state = Q_UNQUOTED
            else:
                buff.append(c)
        elif current_state == Q_ESCAPE:
            # Simple single-character escape sequences such as \" or \\
            buff.append(c)
            current_state = Q_ESCAPE if c == '\\' else Q_QUOTED

    if current_op:
        result.append((
            current_op,
            bytes(buff)
        ))

    return result
