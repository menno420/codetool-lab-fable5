"""Tests for `envdrift lint`."""

import json

from envdrift.cli import main
from envdrift.commands.lint import looks_high_entropy


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


def test_lint_clean(tmp_path, capsys):
    src = write(tmp_path, ".env", "# fine\nA=1\nB=two\n")
    assert main(["lint", src]) == 0
    assert "clean" in capsys.readouterr().out


def test_lint_duplicate_key(tmp_path, capsys):
    src = write(tmp_path, ".env", "A=1\nA=2\n")
    assert main(["lint", src]) == 1
    out = capsys.readouterr().out
    assert "duplicate-key" in out
    assert ":2:" in out


def test_lint_invalid_key(tmp_path, capsys):
    src = write(tmp_path, ".env", "9LIVES=cat\n")
    assert main(["lint", src]) == 1
    assert "invalid-key" in capsys.readouterr().out


def test_lint_space_around_equals(tmp_path, capsys):
    src = write(tmp_path, ".env", "KEY = value\n")
    assert main(["lint", src]) == 1
    assert "space-around-equals" in capsys.readouterr().out


def test_lint_unclosed_quote(tmp_path, capsys):
    src = write(tmp_path, ".env", 'KEY="oops\n')
    assert main(["lint", src]) == 1
    assert "unclosed-quote" in capsys.readouterr().out


def test_lint_invalid_line(tmp_path, capsys):
    src = write(tmp_path, ".env", "not an assignment\n")
    assert main(["lint", src]) == 1
    assert "invalid-line" in capsys.readouterr().out


def test_lint_secret_key_only_with_example_flag(tmp_path, capsys):
    src = write(tmp_path, ".env", "API_KEY=abc123\n")
    assert main(["lint", src]) == 0
    capsys.readouterr()
    assert main(["lint", src, "--example"]) == 1
    assert "secret-key" in capsys.readouterr().out


def test_lint_example_secret_with_empty_value_ok(tmp_path, capsys):
    src = write(tmp_path, ".env.example", "API_KEY=\nDB_PASSWORD=\n")
    assert main(["lint", src, "--example"]) == 0


def test_lint_example_high_entropy_value(tmp_path, capsys):
    src = write(tmp_path, ".env.example", "MYSTERY=a1B2c3D4e5F6g7H8i9J0kL\n")
    assert main(["lint", src, "--example"]) == 1
    assert "high-entropy-value" in capsys.readouterr().out


def test_lint_example_plain_words_not_flagged(tmp_path, capsys):
    src = write(tmp_path, ".env.example", "GREETING=hello\nMODE=development-environment\n")
    assert main(["lint", src, "--example"]) == 0


def test_lint_json_shape(tmp_path, capsys):
    src = write(tmp_path, ".env", "A=1\nA=2\nKEY = v\n")
    assert main(["lint", src, "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "lint"
    assert payload["ok"] is False
    codes = [f["code"] for f in payload["findings"]]
    assert codes == ["duplicate-key", "space-around-equals"]
    assert payload["findings"][0]["line"] == 2
    assert payload["findings"][0]["key"] == "A"
    assert all(set(f) == {"line", "code", "key", "message"} for f in payload["findings"])


def test_lint_missing_file_exit_2(tmp_path, capsys):
    assert main(["lint", str(tmp_path / "ghost.env")]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_high_entropy_heuristic():
    assert looks_high_entropy("deadbeefdeadbeefdead1234")  # hex, 24 chars
    assert looks_high_entropy("QWxhZGRpbjpvcGVuIHNlc2FtZQ==")  # base64
    assert not looks_high_entropy("short")
    assert not looks_high_entropy("just-plain-words-here-really")  # no digits
    assert not looks_high_entropy("has spaces so not a token 12345")
