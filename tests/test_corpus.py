"""Real-world dotenv corpus: one regression test per hardening pattern.

Each case documents behavior for a pattern seen in real .env files.
Every accepted input must also round-trip exactly through render().
"""

import pytest

from envdrift.parser import BOM, parse, parse_file


def assert_round_trip(text):
    assert parse(text).render() == text


def test_multiline_double_quoted_value():
    text = 'CERT="-----BEGIN-----\nline2\n-----END-----"\nAFTER=1\n'
    env = parse(text)
    assert env.as_dict() == {
        "CERT": "-----BEGIN-----\nline2\n-----END-----",
        "AFTER": "1",
    }
    assert env.issues == []
    assert [line.kind for line in env.lines] == ["entry", "entry"]
    # AFTER sits on physical line 4.
    assert env.entries[1].line == 4
    assert_round_trip(text)


def test_multiline_single_quoted_value():
    text = "NOTE='first\nsecond'\n"
    env = parse(text)
    assert env.as_dict() == {"NOTE": "first\nsecond"}
    assert env.issues == []
    assert_round_trip(text)


def test_multiline_with_escaped_quote_inside():
    text = 'MSG="say \\"hi\\"\nand \\"bye\\""\n'
    env = parse(text)
    assert env.as_dict() == {"MSG": 'say "hi"\nand "bye"'}
    assert env.issues == []
    assert_round_trip(text)


def test_multiline_inline_comment_after_close():
    text = 'KEY="a\nb" # note\n'
    env = parse(text)
    assert env.as_dict() == {"KEY": "a\nb"}
    assert env.entries[0].inline_comment == "# note"
    assert_round_trip(text)


def test_multiline_never_closes_falls_back_to_unclosed():
    # No closing quote anywhere: only the first line is consumed, the rest
    # of the file is not swallowed into the value.
    text = 'KEY="never closed\nNEXT=1\n'
    env = parse(text)
    assert env.entries[0].unclosed_quote is True
    assert "unclosed-quote" in [i.code for i in env.issues]
    assert env.as_dict()["NEXT"] == "1"
    assert_round_trip(text)


def test_multiline_crlf_value_uses_lf_line_breaks():
    text = 'CERT="line1\r\nline2"\r\nAFTER=1\r\n'
    env = parse(text)
    # Line breaks inside the value are normalized to \n; raw text round-trips.
    assert env.as_dict() == {"CERT": "line1\nline2", "AFTER": "1"}
    assert env.issues == []
    assert_round_trip(text)


def test_escaped_quotes_inside_quoted_value():
    text = 'MSG="he said \\"hi\\" loudly"\n'
    env = parse(text)
    assert env.as_dict() == {"MSG": 'he said "hi" loudly'}
    assert env.issues == []
    assert_round_trip(text)


def test_export_with_odd_spacing():
    text = "  export   KEY=value\nexport\tTABBED=1\n"
    env = parse(text)
    assert env.as_dict() == {"KEY": "value", "TABBED": "1"}
    assert all(entry.export for entry in env.entries)
    assert env.issues == []
    assert_round_trip(text)


def test_crlf_endings_throughout():
    text = 'A=1\r\nB=two words\r\n# comment\r\nC="quoted"\r\n\r\nD= \r\n'
    env = parse(text)
    # Values never include the trailing \r.
    assert env.as_dict() == {"A": "1", "B": "two words", "C": "quoted", "D": ""}
    assert env.issues == []
    assert_round_trip(text)


def test_crlf_inline_comment():
    text = "PORT=8080 # web\r\n"
    env = parse(text)
    assert env.as_dict() == {"PORT": "8080"}
    assert env.entries[0].inline_comment == "# web"
    assert_round_trip(text)


def test_bom_at_file_start():
    text = BOM + "FIRST=1\nSECOND=2\n"
    env = parse(text)
    # The BOM is not part of the first key.
    assert env.as_dict() == {"FIRST": "1", "SECOND": "2"}
    assert env.issues == []
    assert env.bom is True
    assert_round_trip(text)


def test_bom_via_parse_file(tmp_path):
    path = tmp_path / ".env"
    path.write_bytes(b"\xef\xbb\xbfA=1\n")
    env = parse_file(str(path))
    assert env.as_dict() == {"A": "1"}
    assert env.issues == []
    assert env.render() == BOM + "A=1\n"


def test_parse_file_preserves_crlf(tmp_path):
    path = tmp_path / ".env"
    path.write_bytes(b"A=1\r\nB=2\r\n")
    env = parse_file(str(path))
    assert env.as_dict() == {"A": "1", "B": "2"}
    assert env.render() == "A=1\r\nB=2\r\n"


def test_trailing_whitespace_after_quoted_value():
    text = 'KEY="v"   \n'
    env = parse(text)
    assert env.as_dict() == {"KEY": "v"}
    assert env.issues == []
    assert_round_trip(text)


def test_key_equals_empty_vs_bare_key():
    # KEY= is an empty value; bare KEY (no '=') stays a documented
    # invalid-line finding rather than being guessed at.
    text = "WITHEQ=\nBAREKEY\n"
    env = parse(text)
    assert env.as_dict() == {"WITHEQ": ""}
    assert [(i.line, i.code) for i in env.issues] == [(2, "invalid-line")]
    assert env.lines[1].kind == "invalid"
    assert_round_trip(text)


def test_hash_inside_quoted_values_is_not_comment():
    text = "URL=\"http://host/path#frag\"\nPASS='p#ss'\n"
    env = parse(text)
    assert env.as_dict() == {"URL": "http://host/path#frag", "PASS": "p#ss"}
    assert all(entry.inline_comment is None for entry in env.entries)
    assert env.issues == []
    assert_round_trip(text)


@pytest.mark.parametrize(
    "text",
    [
        'CERT="a\nb\nc"\nX=1\n',
        "NOTE='m\nn'\r\nY=2\r\n",
        BOM + 'A=1\r\nB="x y"\r\n',
        'K="v"  # comment  \nL=\n',
        "  export   PATH_X=/opt  # inline\n\n# end\n",
    ],
)
def test_corpus_round_trip_guarantee(text):
    assert_round_trip(text)
