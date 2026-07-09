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
* Multi-line quoted values: a quoted value that does not close on its own
  line continues across the following lines until the closing quote.
  Line breaks inside the value are ``\\n`` regardless of the file's line
  endings. If the quote never closes anywhere in the file, only the first
  line is consumed and an ``unclosed-quote`` issue is reported.
* CRLF line endings are accepted and preserved on round-trip; parsed
  values never include a trailing ``\\r``.
* A UTF-8 BOM at the start of the file is accepted (and re-emitted by
  :meth:`EnvFile.render`); it is not treated as part of the first key.

Deliberately NOT supported (out of scope, kept simple):
variable interpolation (``${VAR}``), backslash line continuations, and
``KEY value`` / bare ``KEY`` (no ``=``) syntax.

Duplicate keys and invalid key names (valid: ``[A-Za-z_][A-Za-z0-9_]*``)
are detected and reported as issues; parsing still continues.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")

BOM = "\ufeff"

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
    key: str | None = None


@dataclass
class Entry:
    """One ``KEY=value`` assignment."""

    key: str
    value: str  # parsed value (escapes processed for double quotes)
    line: int
    quote: str | None = None  # '"', "'" or None
    export: bool = False
    inline_comment: str | None = None  # includes the leading '#'
    raw_value: str = ""  # value exactly as written (incl. quotes)
    key_valid: bool = True
    unclosed_quote: bool = False
    ws_around_eq: bool = False


@dataclass
class Line:
    """One logical line of the source file.

    A multi-line quoted value is stored as a single ``Line`` whose ``raw``
    contains embedded ``\\n`` separators; ``number`` is its first physical
    line.
    """

    number: int
    raw: str  # without trailing newline
    kind: str  # 'blank' | 'comment' | 'entry' | 'invalid'
    entry: Entry | None = None


@dataclass
class EnvFile:
    """Parsed dotenv file: ordered lines, entries, and issues."""

    lines: list[Line] = field(default_factory=list)
    entries: list[Entry] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    trailing_newline: bool = True
    bom: bool = False  # file started with a UTF-8 BOM

    def ordered_keys(self) -> list[str]:
        """Unique keys in first-occurrence order."""
        seen = set()
        out = []
        for entry in self.entries:
            if entry.key not in seen:
                seen.add(entry.key)
                out.append(entry.key)
        return out

    def as_dict(self) -> dict[str, str]:
        """Key -> value mapping. On duplicates the last assignment wins."""
        return {entry.key: entry.value for entry in self.entries}

    def duplicates(self) -> dict[str, list[int]]:
        """Keys assigned more than once -> their line numbers."""
        positions: dict[str, list[int]] = {}
        for entry in self.entries:
            positions.setdefault(entry.key, []).append(entry.line)
        return {k: v for k, v in positions.items() if len(v) > 1}

    def render(self) -> str:
        """Reconstruct the original text exactly (lossless round-trip)."""
        text = "\n".join(line.raw for line in self.lines)
        if self.lines and self.trailing_newline:
            text += "\n"
        if self.bom:
            text = BOM + text
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


def _split_after_quote(remainder: str, lineno: int, issues: list[Issue], key: str):
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
            message=f"unexpected text after closing quote: {stripped!r}",
            key=key,
        )
    )
    return None


def _parse_quoted(rest: str, quote: str, lineno: int, issues: list[Issue], key: str):
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
        Issue(line=lineno, code="unclosed-quote", message=f"unclosed {quote} quote", key=key)
    )
    value = "".join(chars)
    if quote == '"':
        value = _unescape(value)
    return value, None, True


def _parse_unquoted(rest: str, ws_after: str):
    """Parse an unquoted value. Returns (value, comment).

    An inline comment starts at a ``#`` preceded by whitespace.
    """
    if rest.startswith("#") and ws_after:
        return "", rest.strip()
        # KEY=#value — '#' not preceded by whitespace, part of the value.
    for i, char in enumerate(rest):
        if char == "#" and i > 0 and rest[i - 1] in " \t":
            return rest[:i].rstrip(), rest[i:].strip()
    return rest.rstrip(), None


def _find_close(segment: str, quote: str, start: int) -> int:
    """Index of the closing quote in ``segment`` from ``start``, or -1.

    For double quotes, backslash-escaped quotes do not close.
    """
    i = start
    while i < len(segment):
        char = segment[i]
        if quote == '"' and char == "\\" and i + 1 < len(segment):
            i += 2
            continue
        if char == quote:
            return i
        i += 1
    return -1


def _strip_cr(segment: str) -> str:
    """Drop one trailing carriage return (CRLF line endings)."""
    return segment[:-1] if segment.endswith("\r") else segment


def parse(text: str) -> EnvFile:
    """Parse dotenv text into an :class:`EnvFile`."""
    env = EnvFile()
    if text.startswith(BOM):
        env.bom = True
        text = text[len(BOM) :]
    env.trailing_newline = text.endswith("\n")
    raw_lines = text.split("\n")
    if env.trailing_newline:
        raw_lines = raw_lines[:-1]
    if text == "":
        raw_lines = []

    seen: dict[str, int] = {}
    idx = 0
    while idx < len(raw_lines):
        raw = raw_lines[idx]
        number = idx + 1
        idx += 1
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
                    message=f"not a KEY=value assignment: {stripped!r}",
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
                    message=f"invalid key name: {key!r} (expected [A-Za-z_][A-Za-z0-9_]*)",
                    key=key,
                )
            )

        unclosed = False
        if rest.startswith('"') or rest.startswith("'"):
            quote = rest[0]
            # Multi-line: the quote does not close on this physical line —
            # consume following lines until the line where it closes. If it
            # never closes, fall through to the single-line unclosed path.
            if _find_close(_strip_cr(rest), quote, 1) < 0:
                end = idx  # index of the physical line that closes the quote
                while end < len(raw_lines) and _find_close(raw_lines[end], quote, 0) < 0:
                    end += 1
                if end < len(raw_lines):
                    segments = [rest] + raw_lines[idx : end + 1]
                    rest = "\n".join(_strip_cr(seg) for seg in segments)
                    raw = "\n".join([raw] + raw_lines[idx : end + 1])
                    idx = end + 1
            logical = _strip_cr(rest)
            value, comment, unclosed = _parse_quoted(logical, quote, number, env.issues, key)
            raw_value = _raw_quoted_portion(logical, quote)
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
                    message=f"duplicate key {key!r} (first defined on line {seen[key]})",
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
    """Parse a dotenv file from disk. Raises ``OSError`` if unreadable.

    Opened with ``newline=""`` so CRLF line endings reach the parser (and
    :meth:`EnvFile.render`) untouched instead of being normalized to LF.
    """
    with open(path, encoding="utf-8", newline="") as handle:
        return parse(handle.read())
