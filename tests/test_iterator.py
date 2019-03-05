from simdjson import ParsedJson, Iterator


def test_move_forward():
    pj = ParsedJson(b'{"key": {"list": [0,1]}}')

    it = Iterator(pj)

    r = []
    while True:
        r.append(chr(it.get_type()))
        if not it.move_forward():
            break

    assert r == [
        '{',
        '"',
        '{',
        '"',
        '[',
        'l',
        'l',
        ']',
        '}',
        '}'
    ]
