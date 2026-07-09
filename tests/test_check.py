"""Tests for `envdrift check`."""

import json

from envdrift.cli import main


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


def test_check_clean(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\nB=2\n")
    example = write(tmp_path, ".env.example", "A=\nB=\n")
    assert main(["check", "--env", env, "--example", example]) == 0
    assert "ok:" in capsys.readouterr().out


def test_check_missing_key(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\nB=\n")
    assert main(["check", "--env", env, "--example", example]) == 1
    out = capsys.readouterr().out
    assert "missing: B" in out
    assert "1 missing" in out


def test_check_extra_key(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\nSNEAKY=x\n")
    example = write(tmp_path, ".env.example", "A=\n")
    assert main(["check", "--env", env, "--example", example]) == 1
    assert "extra: SNEAKY" in capsys.readouterr().out


def test_check_allow_extra(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\nSNEAKY=x\n")
    example = write(tmp_path, ".env.example", "A=\n")
    assert main(["check", "--env", env, "--example", example, "--allow-extra"]) == 0


def test_check_required_but_empty(tmp_path, capsys):
    env = write(tmp_path, ".env", "API_KEY=\nOPTIONAL=\n")
    example = write(tmp_path, ".env.example", "API_KEY=placeholder\nOPTIONAL=\n")
    assert main(["check", "--env", env, "--example", example]) == 1
    out = capsys.readouterr().out
    assert "empty: API_KEY" in out
    assert "OPTIONAL" not in out


def test_check_json_shape(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\nEXTRA=x\nE=\n")
    example = write(tmp_path, ".env.example", "A=\nB=\nE=nonempty\n")
    assert main(["check", "--env", env, "--example", example, "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "check"
    assert payload["ok"] is False
    assert payload["missing"] == ["B"]
    assert payload["extra"] == ["EXTRA"]
    assert payload["empty"] == ["E"]
    assert payload["env"] == env
    assert payload["example"] == example


def test_check_json_clean(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\n")
    assert main(["check", "--env", env, "--example", example, "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True


def test_check_missing_file_exit_2(tmp_path, capsys):
    example = write(tmp_path, ".env.example", "A=\n")
    code = main(["check", "--env", str(tmp_path / "nope.env"), "--example", example])
    assert code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "cannot read" in captured.err


def test_check_fix_appends_missing(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\nB=placeholder\n")
    assert main(["check", "--env", env, "--example", example, "--fix"]) == 0
    out = capsys.readouterr().out
    assert "missing: B" in out  # drift still reported first
    assert "fixed: added B" in out
    with open(env, encoding="utf-8") as handle:
        assert handle.read() == "A=1\n# added by envdrift sync\nB=placeholder\n"


def test_check_fix_exit_1_when_unfixable_remains(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\nEXTRA=x\n")
    example = write(tmp_path, ".env.example", "A=\nB=\n")
    assert main(["check", "--env", env, "--example", example, "--fix"]) == 1
    out = capsys.readouterr().out
    assert "fixed: added B" in out
    assert "1 unfixable finding(s) remain" in out


def test_check_fix_never_fixes_empty(tmp_path, capsys):
    env = write(tmp_path, ".env", "API_KEY=\n")
    example = write(tmp_path, ".env.example", "API_KEY=needed\n")
    assert main(["check", "--env", env, "--example", example, "--fix"]) == 1
    with open(env, encoding="utf-8") as handle:
        assert handle.read() == "API_KEY=\n"  # untouched


def test_check_fix_with_allow_extra(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\nEXTRA=x\n")
    example = write(tmp_path, ".env.example", "A=\nB=\n")
    code = main(
        ["check", "--env", env, "--example", example, "--fix", "--allow-extra"]
    )
    assert code == 0


def test_check_fix_clean_is_noop(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\n")
    assert main(["check", "--env", env, "--example", example, "--fix"]) == 0
    assert "ok:" in capsys.readouterr().out
    with open(env, encoding="utf-8") as handle:
        assert handle.read() == "A=1\n"


def test_check_fix_json_shape(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\nE=\n")
    example = write(tmp_path, ".env.example", "A=\nB=\nE=nonempty\n")
    code = main(
        ["check", "--env", env, "--example", example, "--fix", "--format", "json"]
    )
    assert code == 1  # empty: E remains unfixable
    payload = json.loads(capsys.readouterr().out)
    assert payload["missing"] == ["B"]
    assert payload["fixed"] == ["B"]
    assert payload["empty"] == ["E"]
    assert payload["ok"] is False


def test_check_without_fix_has_no_fixed_field(tmp_path, capsys):
    env = write(tmp_path, ".env", "A=1\n")
    example = write(tmp_path, ".env.example", "A=\nB=\n")
    assert main(["check", "--env", env, "--example", example, "--format", "json"]) == 1
    assert "fixed" not in json.loads(capsys.readouterr().out)
