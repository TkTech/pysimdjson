
def test_parser_understands_float(parser):
    doc = parser.parse('1.0')
    assert type(doc) is float


def test_mini_does_not_drop_zero(parser):
    doc = parser.parse(b'[0.0, 0.5, 1.0]')
    assert doc.mini == b'[0.0,0.5,1.0]'
