"""Parser tests: structure, quoting, escapes, issues, round-trips."""

from envdrift.parser import parse


def test_blank_and_comment_lines_preserved():
    env = parse("# header\n\nKEY=1\n")
    kinds = [line.kind for line in env.lines]
    assert kinds == ["comment", "blank", "entry"]
    assert env.lines[0].raw == "# header"


def test_simple_assignment():
    env = parse("NAME=value\n")
    assert env.as_dict() == {"NAME": "value"}
    assert env.entries[0].line == 1
    assert env.entries[0].quote is None
    assert not env.issues


def test_export_prefix():
    env = parse("export PATH_EXTRA=/opt/bin\n")
    entry = env.entries[0]
    assert entry.export is True
    assert entry.key == "PATH_EXTRA"
    assert entry.value == "/opt/bin"


def test_empty_value():
    env = parse("EMPTY=\n")
    assert env.as_dict() == {"EMPTY": ""}


def test_value_containing_equals():
    env = parse("DSN=postgres://u:p@h/db?sslmode=require\n")
    assert env.as_dict()["DSN"] == "postgres://u:p@h/db?sslmode=require"


def test_double_quoted_escapes():
    env = parse('MSG="line1\\nline2\\tend \\"quoted\\" back\\\\slash"\n')
    assert env.as_dict()["MSG"] == 'line1\nline2\tend "quoted" back\\slash'
    assert env.entries[0].quote == '"'


def test_unknown_escape_kept_literal():
    env = parse('X="a\\qb"\n')
    assert env.as_dict()["X"] == "a\\qb"


def test_single_quoted_is_literal():
    env = parse("MSG='no\\nescape # not comment'\n")
    assert env.as_dict()["MSG"] == "no\\nescape # not comment"
    assert env.entries[0].quote == "'"
    assert env.entries[0].inline_comment is None


def test_inline_comment_unquoted():
    env = parse("PORT=8080 # the web port\n")
    entry = env.entries[0]
    assert entry.value == "8080"
    assert entry.inline_comment == "# the web port"


def test_hash_without_preceding_space_is_value():
    env = parse("COLOR=#ff00aa\n")
    assert env.as_dict()["COLOR"] == "#ff00aa"
    assert env.entries[0].inline_comment is None


def test_inline_comment_after_quoted_value():
    env = parse('KEY="v" # note\n')
    assert env.as_dict()["KEY"] == "v"
    assert env.entries[0].inline_comment == "# note"


def test_whitespace_around_equals():
    env = parse("KEY = value\n")
    entry = env.entries[0]
    assert entry.key == "KEY"
    assert entry.value == "value"
    assert entry.ws_around_eq is True


def test_duplicate_keys_detected_with_line_numbers():
    env = parse("A=1\nB=2\nA=3\n")
    assert env.duplicates() == {"A": [1, 3]}
    dup_issues = [i for i in env.issues if i.code == "duplicate-key"]
    assert len(dup_issues) == 1
    assert dup_issues[0].line == 3
    assert "line 1" in dup_issues[0].message
    # last assignment wins
    assert env.as_dict()["A"] == "3"


def test_invalid_key_name():
    env = parse("1BAD=x\n")
    issue_codes = [i.code for i in env.issues]
    assert "invalid-key" in issue_codes
    assert env.entries[0].key_valid is False


def test_invalid_line_without_equals():
    env = parse("JUSTAWORD\n")
    assert env.lines[0].kind == "invalid"
    assert [i.code for i in env.issues] == ["invalid-line"]
    assert env.entries == []


def test_unclosed_quote():
    env = parse('KEY="never closed\n')
    assert env.entries[0].unclosed_quote is True
    assert "unclosed-quote" in [i.code for i in env.issues]


def test_trailing_junk_after_quote():
    env = parse('KEY="v" garbage\n')
    assert env.as_dict()["KEY"] == "v"
    assert "trailing-junk" in [i.code for i in env.issues]


def test_line_numbers_skip_comments_and_blanks():
    env = parse("# one\n\nA=1\n# four\nB=2\n")
    assert [e.line for e in env.entries] == [3, 5]


def test_render_round_trip_exact():
    text = '# header\n\nexport A=1\nB = "two"  # note\nC=\'lit\'\nWEIRD KEY\n'
    assert parse(text).render() == text


def test_render_round_trip_no_trailing_newline():
    text = "A=1\nB=2"
    assert parse(text).render() == text


def test_empty_input():
    env = parse("")
    assert env.lines == []
    assert env.render() == ""


def test_keys_first_occurrence_order():
    env = parse("Z=1\nA=2\nZ=3\n")
    assert env.ordered_keys() == ["Z", "A"]
