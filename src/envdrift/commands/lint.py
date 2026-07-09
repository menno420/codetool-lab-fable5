"""``envdrift lint`` — find common dotenv mistakes.

Base checks: duplicate keys, invalid key names, invalid lines,
whitespace around ``=``, unclosed quotes, junk after a closing quote.

With ``--example`` (for files meant to be committed, like .env.example):
flags likely secrets — keys matching
``(?i)(secret|token|password|passwd|api_?key|private)`` with a non-empty
value, and values that look high-entropy (20+ chars of base64/hex
containing both letters and digits).
"""

from __future__ import annotations

import re

from envdrift.commands import EXIT_FINDINGS, EXIT_OK, emit_json, load

SECRET_KEY_RE = re.compile(r"(?i)(secret|token|password|passwd|api_?key|private)")
HEX_RE = re.compile(r"[0-9a-fA-F]{20,}\Z")
BASE64ISH_RE = re.compile(r"[A-Za-z0-9+/_-]{20,}={0,2}\Z")


def looks_high_entropy(value: str) -> bool:
    if len(value) < 20:
        return False
    if HEX_RE.match(value) and re.search(r"[0-9]", value) and re.search(r"[a-fA-F]", value):
        return True
    return bool(
        BASE64ISH_RE.match(value)
        and re.search(r"[0-9]", value)
        and re.search(r"[A-Za-z]", value)
    )


def run(args) -> int:
    env = load(args.file)
    findings = [
        {"line": issue.line, "code": issue.code, "key": issue.key, "message": issue.message}
        for issue in env.issues
    ]

    for entry in env.entries:
        if entry.ws_around_eq:
            findings.append(
                {
                    "line": entry.line,
                    "code": "space-around-equals",
                    "key": entry.key,
                    "message": f"whitespace around '=' in {entry.key} (most loaders reject or "
                    "misread this)",
                }
            )
        if args.example and entry.value:
            if SECRET_KEY_RE.search(entry.key):
                findings.append(
                    {
                        "line": entry.line,
                        "code": "secret-key",
                        "key": entry.key,
                        "message": f"{entry.key} looks like a secret but has a non-empty value "
                        "in an example file",
                    }
                )
            elif looks_high_entropy(entry.value):
                findings.append(
                    {
                        "line": entry.line,
                        "code": "high-entropy-value",
                        "key": entry.key,
                        "message": f"value of {entry.key} looks high-entropy (possible secret) "
                        "in an example file",
                    }
                )

    findings.sort(key=lambda f: (f["line"], f["code"]))
    ok = not findings

    if args.format == "json":
        emit_json({"command": "lint", "file": args.file, "ok": ok, "findings": findings})
    else:
        if ok:
            print(f"ok: {args.file} is clean")
        else:
            for finding in findings:
                print(
                    f"{args.file}:{finding['line']}: {finding['code']}: {finding['message']}"
                )
            print(f"{len(findings)} finding(s)")
    return EXIT_OK if ok else EXIT_FINDINGS
