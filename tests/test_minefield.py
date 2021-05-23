"""Test simdjson against the JSON minefield by Nicholas Seriot.

See https://github.com/nst/JSONTestSuite for more.
"""


def test_parsing(parser, parsing_tests):
    """Ensure all parsing tests complete as expected."""
    for expected_result, files in parsing_tests.items():
        for file in files:
            try:
                parser.load(file)
            except ValueError:
                # The source document was not expected to fail.
                if expected_result == 'y':
                    raise
