"""Tests for global CLI behaviour."""

import pytest

from envdrift import __version__
from envdrift.cli import main


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert capsys.readouterr().out.strip() == f"envdrift {__version__}"


def test_no_command_is_usage_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2
    assert "usage" in capsys.readouterr().err.lower()


def test_unknown_command_is_usage_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["frobnicate"])
    assert excinfo.value.code == 2


@pytest.mark.parametrize("cmd", ["check", "diff", "example", "lint"])
def test_subcommand_help(cmd, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([cmd, "--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "usage" in out.lower()
    assert cmd in out


def test_bad_format_choice_is_usage_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["check", "--format", "yaml"])
    assert excinfo.value.code == 2
