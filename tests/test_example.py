"""Tests for `envdrift example`."""

from envdrift.cli import main

SOURCE = (
    "# Database settings\n"
    "DB_HOST=localhost\n"
    'DB_PASSWORD="s3cret!"\n'
    "\n"
    "# Web\n"
    "export PORT=8080 # dev port\n"
    "LOG_LEVEL=info\n"
)


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


def test_example_strips_values_preserves_structure(tmp_path, capsys):
    src = write(tmp_path, ".env", SOURCE)
    assert main(["example", src]) == 0
    out = capsys.readouterr().out
    assert out == (
        "# Database settings\n"
        "DB_HOST=\n"
        "DB_PASSWORD=\n"
        "\n"
        "# Web\n"
        "export PORT= # dev port\n"
        "LOG_LEVEL=\n"
    )


def test_example_keep_values_for(tmp_path, capsys):
    src = write(tmp_path, ".env", SOURCE)
    assert main(["example", src, "--keep-values-for", "^(PORT|LOG_LEVEL)$"]) == 0
    out = capsys.readouterr().out
    assert "export PORT=8080 # dev port" in out
    assert "LOG_LEVEL=info" in out
    assert "s3cret" not in out
    assert "DB_HOST=\n" in out


def test_example_keep_values_preserves_quotes(tmp_path, capsys):
    src = write(tmp_path, ".env", 'GREETING="hello world"\n')
    assert main(["example", src, "--keep-values-for", "GREETING"]) == 0
    assert capsys.readouterr().out == 'GREETING="hello world"\n'


def test_example_output_file(tmp_path, capsys):
    src = write(tmp_path, ".env", SOURCE)
    dest = tmp_path / ".env.example"
    assert main(["example", src, "-o", str(dest)]) == 0
    assert capsys.readouterr().out == ""
    assert "DB_PASSWORD=\n" in dest.read_text()


def test_example_bad_regex_exit_2(tmp_path, capsys):
    src = write(tmp_path, ".env", "A=1\n")
    assert main(["example", src, "--keep-values-for", "["]) == 2
    assert "invalid --keep-values-for regex" in capsys.readouterr().err


def test_example_missing_file_exit_2(tmp_path, capsys):
    assert main(["example", str(tmp_path / "nope.env")]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_example_round_trips_through_check(tmp_path, capsys):
    """A generated example must pass `check` against its source env."""
    src = write(tmp_path, ".env", SOURCE)
    dest = tmp_path / ".env.example"
    assert main(["example", src, "-o", str(dest)]) == 0
    assert main(["check", "--env", src, "--example", str(dest)]) == 0
