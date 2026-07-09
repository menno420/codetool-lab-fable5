"""``envdrift example`` — generate a .env.example from a real .env.

Values are stripped to empty by default: envdrift never guesses which
values are "safe" to publish. Use ``--keep-values-for REGEX`` to keep
values for non-secret keys (e.g. ``--keep-values-for '^(PORT|LOG_LEVEL)$'``).
"""

from __future__ import annotations

import re
import sys

from envdrift.commands import EXIT_OK, CliError, load
from envdrift.parser import BOM, EnvFile


def generate(env: EnvFile, keep_pattern=None) -> str:
    out = []
    for line in env.lines:
        if line.kind != "entry":
            out.append(line.raw)
            continue
        entry = line.entry
        keep = keep_pattern is not None and keep_pattern.search(entry.key)
        value = entry.raw_value if keep else ""
        prefix = "export " if entry.export else ""
        comment = " " + entry.inline_comment if entry.inline_comment else ""
        # Entry lines are rewritten; keep the CRLF ending if the source had one.
        cr = "\r" if line.raw.endswith("\r") else ""
        out.append(f"{prefix}{entry.key}={value}{comment}{cr}")
    text = "\n".join(out)
    if env.lines and env.trailing_newline:
        text += "\n"
    if env.bom:
        text = BOM + text
    return text


def run(args) -> int:
    keep_pattern = None
    if args.keep_values_for is not None:
        try:
            keep_pattern = re.compile(args.keep_values_for)
        except re.error as exc:
            raise CliError(f"invalid --keep-values-for regex: {exc}") from exc

    env = load(args.envfile)
    text = generate(env, keep_pattern)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
        except OSError as exc:
            raise CliError(f"cannot write {args.output}: {exc.strerror or exc}") from exc
    else:
        sys.stdout.write(text)
    return EXIT_OK
