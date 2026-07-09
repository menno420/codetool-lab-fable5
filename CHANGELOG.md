# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/menno420/codetool-lab-fable5/releases/tag/v0.1.0
