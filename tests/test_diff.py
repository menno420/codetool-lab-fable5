"""Tests for `envdrift diff`."""

import json

from envdrift.cli import main


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


def test_diff_identical(tmp_path, capsys):
    a = write(tmp_path, "a.env", "X=1\nY=2\n")
    b = write(tmp_path, "b.env", "X=1\nY=2\n")
    assert main(["diff", a, b]) == 0
    assert "identical" in capsys.readouterr().out


def test_diff_added_removed_changed(tmp_path, capsys):
    a = write(tmp_path, "a.env", "KEEP=1\nGONE=x\nCHANGED=old\n")
    b = write(tmp_path, "b.env", "KEEP=1\nCHANGED=new\nNEW=y\n")
    assert main(["diff", a, b]) == 1
    out = capsys.readouterr().out
    assert "+ NEW" in out
    assert "- GONE" in out
    assert "~ CHANGED: <changed>" in out


def test_diff_hides_values_by_default(tmp_path, capsys):
    a = write(tmp_path, "a.env", "TOKEN=hunter2\n")
    b = write(tmp_path, "b.env", "TOKEN=hunter3\n")
    assert main(["diff", a, b]) == 1
    out = capsys.readouterr().out
    assert "hunter2" not in out
    assert "hunter3" not in out
    assert "<changed>" in out


def test_diff_values_flag_reveals(tmp_path, capsys):
    a = write(tmp_path, "a.env", "TOKEN=hunter2\n")
    b = write(tmp_path, "b.env", "TOKEN=hunter3\n")
    assert main(["diff", a, b, "--values"]) == 1
    out = capsys.readouterr().out
    assert "'hunter2' -> 'hunter3'" in out


def test_diff_json_shape_no_values(tmp_path, capsys):
    a = write(tmp_path, "a.env", "GONE=x\nSAME=1\nCH=a\n")
    b = write(tmp_path, "b.env", "SAME=1\nCH=b\nNEW=y\n")
    assert main(["diff", a, b, "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "diff"
    assert payload["ok"] is False
    assert payload["added"] == [{"key": "NEW"}]
    assert payload["removed"] == [{"key": "GONE"}]
    assert payload["changed"] == [{"key": "CH"}]


def test_diff_json_with_values(tmp_path, capsys):
    a = write(tmp_path, "a.env", "CH=a\n")
    b = write(tmp_path, "b.env", "CH=b\nNEW=v\n")
    assert main(["diff", a, b, "--values", "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["added"] == [{"key": "NEW", "value": "v"}]
    assert payload["changed"] == [{"key": "CH", "old": "a", "new": "b"}]


def test_diff_json_identical_ok(tmp_path, capsys):
    a = write(tmp_path, "a.env", "X=1\n")
    b = write(tmp_path, "b.env", "X=1\n")
    assert main(["diff", a, b, "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["added"] == []


def test_diff_missing_file_exit_2(tmp_path, capsys):
    a = write(tmp_path, "a.env", "X=1\n")
    assert main(["diff", a, str(tmp_path / "missing.env")]) == 2
    assert "cannot read" in capsys.readouterr().err
