Performance
===========

pysimdjson is fast, typically tying or beating all other Python JSON libraries
when simply using :func:`simdjson.loads()` or :func:`simdjson.load()`.

However, 95% of the time spent loading a JSON document into Python is spent in
the creation of Python objects, not the actual parsing of the document. You can
avoid all of this overhead by ignoring parts of the document you don't want.

pysimdjson also has optimizations for loading homogeneous arrays into tools
like `numpy`_ via :func:`simdjson.Array.as_buffer()`. This is typically at
least 8x faster than other methods.

Don't load the entire document
------------------------------

pysimdjson supports this in two ways - the use of JSON pointers via
`at_pointer()`, or proxies for objects and lists.

.. code:: python

    import simdjson
    parser = simdjson.Parser()
    doc = parser.parse(b'{"res": [{"name": "first"}, {"name": "second"}]}')

For our sample above, we really just want the second entry in `res`, we
don't care about anything else. We can do this two ways:

.. code:: python

    assert doc['res'][1]['name'] == 'second' # True
    assert doc.at_pointer('/res/1/name') == 'second' # True

Both of these approaches will be much faster than using `load/s()`, since
they avoid loading the parts of the document we didn't care about.

Both `Object` and `Array` have a `mini` property that returns their entire
content as a minified Python `str`. A message router for example would only
parse the document and retrieve a single property, the destination, and forward
the payload without ever turning it into a Python object. Here's a (bad)
example:

.. code:: python

    import simdjson

    @app.route('/store', methods=['POST'])
    def store():
        parser = simdjson.Parser()
        doc = parser.parse(request.data)
        redis.set(doc['key'], doc.mini)

With this, doc could contain thousands of objects, but the only one loaded
into a python object was `key`, and we even minified the content as we went.

Re-use the parser
-----------------

One of the easiest performance gains if you're working on many documents is
to re-use the parser.

.. code:: python

    import simdjson
    parser = simdjson.Parser()

    for i in range(0, 100):
        doc = parser.parse(b'{"a": "b"}')

This will drastically reduce the number of allocations being made, as it will
reuse the existing buffer when possible. If it's too small, it'll grow to fit.

.. _numpy: https://numpy.org/
