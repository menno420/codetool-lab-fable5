# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-09

### Added

- `envdrift sync` — append keys missing from `.env` at the end of the file
  under a `# added by envdrift sync` comment, using the example's value
  verbatim as the placeholder (`.env.example` is non-secret by design, so
  its values are safe scaffolding defaults). Never modifies, overwrites,
  or reorders existing content; creates the env file if absent; matches
  CRLF line endings. `--dry-run` prints what would be added and writes
  nothing (exit 1 if changes would be made, 0 if in sync). Text and JSON
  output.
- `envdrift check --fix` — after reporting drift, appends the missing keys
  exactly as `sync` does; `extra` and `empty` findings are reported but
  never auto-fixed. Exit 0 if everything fixable was fixed and nothing
  unfixable remains, 1 if unfixable drift remains, 2 on errors. JSON
  output gains a `"fixed"` list.
- Parser: multi-line quoted values — a quoted value that does not close on
  its own line now continues across lines to the closing quote (0.1.0
  truncated the value at the first line and reported spurious
  `unclosed-quote`/`invalid-line` issues). If the quote never closes, only
  the first line is consumed and `unclosed-quote` is reported, as before.
- Parser: a UTF-8 BOM at the start of the file is accepted and preserved
  on round-trip (0.1.0 treated it as part of the first key, producing a
  bogus `invalid-key` and key-name mismatches in `check`).
- Parser: files are read with line endings intact; CRLF files round-trip
  byte-for-byte through `render()` and `example` output (0.1.0 silently
  normalized CRLF to LF when reading from disk). Parsed values never
  include a trailing `\r`.
- Real-world dotenv corpus regression tests: multi-line values, escaped
  quotes, `export` with odd spacing, CRLF throughout, BOM, trailing
  whitespace after quoted values, `KEY=` vs bare `KEY`, `#` inside quoted
  values.
- README: `sync` and `check --fix` documentation with per-command exit
  codes, a pre-commit `repo: local` hook recipe, and an updated GitHub
  Actions recipe.

## [0.1.0] - 2026-07-09

### Added

- Dotenv parser for the common dialect: comments (standalone and inline),
  blank lines, `export ` prefix, single/double/no quotes, escape processing
  in double quotes, values containing `=`, line-number tracking, duplicate
  and invalid-key detection, lossless round-trip rendering.
- `envdrift check` — detect drift between `.env` and `.env.example`
  (missing keys, extra keys, required-but-empty keys), `--allow-extra`,
  text and JSON output.
- `envdrift diff` — key-level diff between two env files (added, removed,
  changed); values hidden by default, revealed with `--values`.
- `envdrift example` — generate a `.env.example` from a real `.env`,
  preserving comments, blank lines, and key order while stripping all
  values; `--keep-values-for REGEX` to keep non-secret values.
- `envdrift lint` — duplicate keys, invalid key names, whitespace around
  `=`, unclosed quotes, invalid lines; with `--example`, likely-secret
  detection (secret-sounding key names, high-entropy values).
- CI: ruff + pytest on Python 3.9–3.13.

[0.2.0]: https://github.com/menno420/codetool-lab-fable5/releases/tag/v0.2.0
[0.1.0]: https://github.com/menno420/codetool-lab-fable5/releases/tag/v0.1.0
