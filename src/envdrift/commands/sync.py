"""``envdrift sync`` — write missing keys into .env from the example.

Missing keys are appended at the end of the env file under a
``# added by envdrift sync`` comment, using the example's value verbatim
as the placeholder: ``.env.example`` is non-secret by design, so its
values are safe scaffolding defaults. Existing keys and values are never
modified, overwritten, or reordered — the file is preserved byte-for-byte
apart from the appended block (and a terminating newline if the file did
not end with one). The env file is created if absent.

Exit codes: without ``--dry-run`` — 0 on success (including "nothing to
add"), 2 on errors. With ``--dry-run`` — 1 if changes would be made,
0 if in sync, 2 on errors (CI-friendly, mirrors ``check``).
"""

from __future__ import annotations

import os

from envdrift.commands import EXIT_FINDINGS, EXIT_OK, CliError, emit_json, load
from envdrift.parser import Entry, EnvFile

SYNC_COMMENT = "# added by envdrift sync"


def missing_entries(env_map: dict, example: EnvFile) -> list[Entry]:
    """Example entries for keys absent from ``env_map``, in example order.

    On duplicate keys in the example, the last assignment wins (matching
    :meth:`EnvFile.as_dict` semantics).
    """
    by_key = {entry.key: entry for entry in example.entries}
    return [by_key[key] for key in example.ordered_keys() if key not in env_map]


def format_entry(entry: Entry) -> str:
    """Render an example entry as an assignment line, value verbatim."""
    prefix = "export " if entry.export else ""
    return f"{prefix}{entry.key}={entry.raw_value}"


def append_missing(env_path: str, entries: list[Entry]) -> bool:
    """Append ``entries`` to ``env_path`` under the sync comment.

    Existing content is untouched (a terminating newline is added first if
    the file does not end with one). Matches the file's CRLF line endings
    when present. Creates the file if absent. Returns True if the file was
    created. Raises :class:`CliError` on read/write failures.
    """
    try:
        with open(env_path, encoding="utf-8", newline="") as handle:
            existing = handle.read()
        created = False
    except FileNotFoundError:
        existing = ""
        created = True
    except OSError as exc:
        raise CliError(f"cannot read {env_path}: {exc.strerror or exc}") from exc

    eol = "\r\n" if "\r\n" in existing else "\n"
    lines = [SYNC_COMMENT] + [format_entry(entry) for entry in entries]
    block = eol.join(line.replace("\n", eol) for line in lines) + eol
    if existing and not existing.endswith("\n"):
        block = eol + block

    try:
        with open(env_path, "a", encoding="utf-8", newline="") as handle:
            handle.write(block)
    except OSError as exc:
        raise CliError(f"cannot write {env_path}: {exc.strerror or exc}") from exc
    return created


def load_env_or_empty(path: str) -> EnvFile:
    """Parse ``path``; a missing file is an empty env (sync will create it)."""
    try:
        return load(path)
    except CliError:
        if os.path.exists(path):
            raise
        return EnvFile()


def run(args) -> int:
    example = load(args.example)
    env = load_env_or_empty(args.env)

    entries = missing_entries(env.as_dict(), example)
    keys = [entry.key for entry in entries]
    in_sync = not keys

    created = False
    if entries and not args.dry_run:
        created = append_missing(args.env, entries)

    if args.format == "json":
        emit_json(
            {
                "command": "sync",
                "env": args.env,
                "example": args.example,
                "dry_run": args.dry_run,
                "ok": in_sync if args.dry_run else True,
                "added": keys,
                "created": created,
            }
        )
    elif in_sync:
        print(f"ok: {args.env} is in sync with {args.example}")
    elif args.dry_run:
        for key in keys:
            print(f"would add: {key} (from {args.example})")
        print(f"sync: would add {len(keys)} key(s) to {args.env} (dry-run)")
    else:
        for key in keys:
            print(f"added: {key}")
        suffix = " (created)" if created else ""
        print(f"sync: added {len(keys)} key(s) to {args.env}{suffix}")

    if args.dry_run:
        return EXIT_OK if in_sync else EXIT_FINDINGS
    return EXIT_OK
