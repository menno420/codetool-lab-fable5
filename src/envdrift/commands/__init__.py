"""Subcommand implementations for the envdrift CLI."""

from __future__ import annotations

import json
import sys

from envdrift.parser import EnvFile, parse_file

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


class CliError(Exception):
    """Fatal usage/file error; message goes to stderr, exit code 2."""


def load(path: str) -> EnvFile:
    try:
        return parse_file(path)
    except OSError as exc:
        raise CliError(f"cannot read {path}: {exc.strerror or exc}") from exc


def emit_json(payload: dict) -> None:
    json.dump(payload, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")
