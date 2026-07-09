"""Tests for `envdrift sync`."""

import json

from envdrift.cli import main


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


def read(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def test_sync_appends_missing_keys(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\nB=placeholder\nC=\n")
    assert main(["sync", "--env", env, "--example", example]) == 0
    out = capsys.readouterr().out
    assert "added: B" in out
    assert "added: C" in out
    assert "added 2 key(s)" in out
    assert read(env) == "A=1\n# added by envdrift sync\nB=placeholder\nC=\n"


def test_sync_in_sync_is_noop(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\n")
    assert main(["sync", "--env", env, "--example", example]) == 0
    assert "ok:" in capsys.readouterr().out
    assert read(env) == "A=1\n"


def test_sync_never_touches_existing_values(tmp_path, capsys):
    original = "# mine\nA=real-secret\n\nB = spaced\n"
    env = write(tmp_path, ".env", original)
    example = write(tmp_path, ".env.example", "A=\nB=\nNEW=default\n")
    assert main(["sync", "--env", env, "--example", example]) == 0
    # Existing content preserved byte-for-byte; block appended at the end.
    assert read(env) == original + "# added by envdrift sync\nNEW=default\n"


def test_sync_uses_example_value_verbatim(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(
        tmp_path, ".env.example", 'A=\nQ="quoted # val"\nexport E=exported\n'
    )
    assert main(["sync", "--env", env, "--example", example]) == 0
    assert read(env) == (
        'A=1\n# added by envdrift sync\nQ="quoted # val"\nexport E=exported\n'
    )


def test_sync_creates_env_file(tmp_path, capsys):
    env = str(tmp_path / ".env")
    example = write(tmp_path, ".env.example", "A=x\nB=\n")
    assert main(["sync", "--env", env, "--example", example]) == 0
    assert "(created)" in capsys.readouterr().out
    assert read(env) == "# added by envdrift sync\nA=x\nB=\n"


def test_sync_adds_newline_if_file_lacks_one(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1")  # no trailing newline
    example = write(tmp_path, ".env.example", "A=\nB=\n")
    assert main(["sync", "--env", env, "--example", example]) == 0
    assert read(env) == "A=1\n# added by envdrift sync\nB=\n"


def test_sync_matches_crlf_line_endings(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_bytes(b"A=1\r\n")
    example = write(tmp_path, ".env.example", "A=\nB=x\n")
    assert main(["sync", "--env", str(env), "--example", example]) == 0
    assert env.read_bytes() == b"A=1\r\n# added by envdrift sync\r\nB=x\r\n"


def test_sync_dry_run_exit_1_and_writes_nothing(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\nB=\n")
    assert main(["sync", "--env", env, "--example", example, "--dry-run"]) == 1
    out = capsys.readouterr().out
    assert "would add: B" in out
    assert read(env) == "A=1\n"


def test_sync_dry_run_exit_0_when_in_sync(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\n")
    assert main(["sync", "--env", env, "--example", example, "--dry-run"]) == 0
    assert "ok:" in capsys.readouterr().out


def test_sync_json_shape(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\nB=x\n")
    assert main(["sync", "--env", env, "--example", example, "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "sync"
    assert payload["ok"] is True
    assert payload["dry_run"] is False
    assert payload["added"] == ["B"]
    assert payload["created"] is False


def test_sync_dry_run_json_ok_false_when_out_of_sync(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\nB=\n")
    code = main(
        ["sync", "--env", env, "--example", example, "--dry-run", "--format", "json"]
    )
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["added"] == ["B"]


def test_sync_missing_example_exit_2(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    code = main(["sync", "--env", env, "--example", str(tmp_path / "nope")])
    assert code == 2
    assert "cannot read" in capsys.readouterr().err


def test_sync_is_idempotent(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\nB=x\n")
    assert main(["sync", "--env", env, "--example", example]) == 0
    after_first = read(env)
    assert main(["sync", "--env", env, "--example", example]) == 0
    assert read(env) == after_first  # second run adds nothing
    assert main(["check", "--env", env, "--example", example]) == 0
