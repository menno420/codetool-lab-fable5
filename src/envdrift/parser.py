"""Parser for the common dotenv dialect.

Supported dialect
-----------------
* Blank lines and full-line comments (``# ...``), preserved with positions.
* ``KEY=value`` and ``export KEY=value``.
* Unquoted, single-quoted, and double-quoted values.
* Double-quoted values process the standard escapes ``\\n``, ``\\t``,
  ``\\\\`` and ``\\"``; unknown escapes are kept literally.
* Single-quoted values are literal (no escape processing).
* Unquoted values may contain ``=``; a trailing inline comment is stripped
  only when the ``#`` is preceded by whitespace.
* Empty values (``KEY=``) and whitespace around ``=`` are accepted
  (the latter is flagged by ``envdrift lint``).

Deliberately NOT supported (out of scope, kept simple): multi-line values,
variable interpolation (``${VAR}``), backslash line continuations, and
``KEY value`` (no ``=``) syntax.

Duplicate keys and invalid key names (valid: ``[A-Za-z_][A-Za-z0-9_]*``)
are detected and reported as issues; parsing still continues.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")

# A line that looks like an assignment: optional indent, optional `export `,
# a key token (anything except whitespace/=/#), optional spaces, `=`, rest.
_ENTRY_RE = re.compile(
    r"""^(?P<indent>\s*)
        (?P<export>export\s+)?
        (?P<key>[^\s=#]+)
        (?P<ws_before>[ \t]*)
        =
        (?P<ws_after>[ \t]*)
        (?P<rest>.*)$""",
    re.VERBOSE,
)

_ESCAPES = {"n": "\n", "t": "\t", "\\": "\\", '"': '"'}


@dataclass
class Issue:
    """A problem found while parsing (also consumed by ``envdrift lint``)."""

    line: int
    code: str
    message: str
    key: Optional[str] = None


@dataclass
class Entry:
    """One ``KEY=value`` assignment."""

    key: str
    value: str  # parsed value (escapes processed for double quotes)
    line: int
    quote: Optional[str] = None  # '"', "'" or None
    export: bool = False
    inline_comment: Optional[str] = None  # includes the leading '#'
    raw_value: str = ""  # value exactly as written (incl. quotes)
    key_valid: bool = True
    unclosed_quote: bool = False
    ws_around_eq: bool = False


@dataclass
class Line:
    """One physical line of the source file."""

    number: int
    raw: str  # without trailing newline
    kind: str  # 'blank' | 'comment' | 'entry' | 'invalid'
    entry: Optional[Entry] = None


@dataclass
class EnvFile:
    """Parsed dotenv file: ordered lines, entries, and issues."""

    lines: List[Line] = field(default_factory=list)
    entries: List[Entry] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    trailing_newline: bool = True

    def keys(self) -> List[str]:
        """Unique keys in first-occurrence order."""
        seen = set()
        out = []
        for entry in self.entries:
            if entry.key not in seen:
                seen.add(entry.key)
                out.append(entry.key)
        return out

    def as_dict(self) -> Dict[str, str]:
        """Key -> value mapping. On duplicates the last assignment wins."""
        return {entry.key: entry.value for entry in self.entries}

    def duplicates(self) -> Dict[str, List[int]]:
        """Keys assigned more than once -> their line numbers."""
        positions: Dict[str, List[int]] = {}
        for entry in self.entries:
            positions.setdefault(entry.key, []).append(entry.line)
        return {k: v for k, v in positions.items() if len(v) > 1}

    def render(self) -> str:
        """Reconstruct the original text exactly (lossless round-trip)."""
        text = "\n".join(line.raw for line in self.lines)
        if self.lines and self.trailing_newline:
            text += "\n"
        return text


def _unescape(value: str) -> str:
    out = []
    i = 0
    while i < len(value):
        char = value[i]
        if char == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            if nxt in _ESCAPES:
                out.append(_ESCAPES[nxt])
                i += 2
                continue
        out.append(char)
        i += 1
    return "".join(out)


def _split_after_quote(remainder: str, lineno: int, issues: List[Issue], key: str):
    """Handle text after a closing quote: inline comment or junk."""
    stripped = remainder.strip()
    if not stripped:
        return None
    if stripped.startswith("#"):
        return stripped
    issues.append(
        Issue(
            line=lineno,
            code="trailing-junk",
            message="unexpected text after closing quote: %r" % stripped,
            key=key,
        )
    )
    return None


def _parse_quoted(rest: str, quote: str, lineno: int, issues: List[Issue], key: str):
    """Parse a value starting with a quote char. Returns (value, comment, unclosed)."""
    i = 1
    chars = []
    while i < len(rest):
        char = rest[i]
        if quote == '"' and char == "\\" and i + 1 < len(rest):
            chars.append(rest[i : i + 2])
            i += 2
            continue
        if char == quote:
            value = "".join(chars)
            if quote == '"':
                value = _unescape(value)
            comment = _split_after_quote(rest[i + 1 :], lineno, issues, key)
            return value, comment, False
        chars.append(char)
        i += 1
    issues.append(
        Issue(line=lineno, code="unclosed-quote", message="unclosed %s quote" % quote, key=key)
    )
    value = "".join(chars)
    if quote == '"':
        value = _unescape(value)
    return value, None, True


def _parse_unquoted(rest: str, ws_after: str):
    """Parse an unquoted value. Returns (value, comment).

    An inline comment starts at a ``#`` preceded by whitespace.
    """
    if rest.startswith("#"):
        if ws_after:
            return "", rest.strip()
        # KEY=#value — '#' not preceded by whitespace, part of the value.
    for i, char in enumerate(rest):
        if char == "#" and i > 0 and rest[i - 1] in " \t":
            return rest[:i].rstrip(), rest[i:].strip()
    return rest.rstrip(), None


def parse(text: str) -> EnvFile:
    """Parse dotenv text into an :class:`EnvFile`."""
    env = EnvFile()
    env.trailing_newline = text.endswith("\n")
    raw_lines = text.split("\n")
    if env.trailing_newline:
        raw_lines = raw_lines[:-1]
    if text == "":
        raw_lines = []

    seen: Dict[str, int] = {}
    for number, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped:
            env.lines.append(Line(number=number, raw=raw, kind="blank"))
            continue
        if stripped.startswith("#"):
            env.lines.append(Line(number=number, raw=raw, kind="comment"))
            continue

        match = _ENTRY_RE.match(raw)
        if match is None:
            env.lines.append(Line(number=number, raw=raw, kind="invalid"))
            env.issues.append(
                Issue(
                    line=number,
                    code="invalid-line",
                    message="not a KEY=value assignment: %r" % stripped,
                )
            )
            continue

        key = match.group("key")
        export = bool(match.group("export"))
        ws_before = match.group("ws_before")
        ws_after = match.group("ws_after")
        rest = match.group("rest")

        key_valid = KEY_RE.match(key) is not None
        if not key_valid:
            env.issues.append(
                Issue(
                    line=number,
                    code="invalid-key",
                    message="invalid key name: %r (expected [A-Za-z_][A-Za-z0-9_]*)" % key,
                    key=key,
                )
            )

        unclosed = False
        if rest.startswith('"') or rest.startswith("'"):
            quote = rest[0]
            value, comment, unclosed = _parse_quoted(rest, quote, number, env.issues, key)
            raw_value = _raw_quoted_portion(rest, quote)
        else:
            quote = None
            value, comment = _parse_unquoted(rest, ws_after)
            raw_value = value  # unquoted raw == parsed (no escapes)

        entry = Entry(
            key=key,
            value=value,
            line=number,
            quote=quote,
            export=export,
            inline_comment=comment,
            raw_value=raw_value,
            key_valid=key_valid,
            unclosed_quote=unclosed,
            ws_around_eq=bool(ws_before or ws_after),
        )
        if key in seen:
            env.issues.append(
                Issue(
                    line=number,
                    code="duplicate-key",
                    message="duplicate key %r (first defined on line %d)" % (key, seen[key]),
                    key=key,
                )
            )
        else:
            seen[key] = number
        env.entries.append(entry)
        env.lines.append(Line(number=number, raw=raw, kind="entry", entry=entry))
    return env


def _raw_quoted_portion(rest: str, quote: str) -> str:
    """Return the quoted token exactly as written, including quotes."""
    i = 1
    while i < len(rest):
        char = rest[i]
        if quote == '"' and char == "\\" and i + 1 < len(rest):
            i += 2
            continue
        if char == quote:
            return rest[: i + 1]
        i += 1
    return rest  # unclosed: everything is the raw value


def parse_file(path: str) -> EnvFile:
    """Parse a dotenv file from disk. Raises ``OSError`` if unreadable."""
    with open(path, encoding="utf-8") as handle:
        return parse(handle.read())
