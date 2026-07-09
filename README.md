# envdrift

**Keep your `.env` files honest.**

envdrift is a zero-dependency command-line tool that detects drift between
your real `.env` and the committed `.env.example`, diffs env files across
machines or environments, generates safe example files, and lints for the
dotenv mistakes that bite in production. Python 3.9+, standard library only.

> Note: the `control/` directory in this repository is unrelated
> fleet-coordination metadata for the project's manager — it is not part of
> the envdrift package.

## Why

`.env` files drift. Someone adds `STRIPE_WEBHOOK_SECRET` to production and
forgets to add it to `.env.example`; the next engineer clones the repo, the
app boots, and payment webhooks silently fail. Or worse: someone generates
`.env.example` by copying `.env` — and commits a live API key. envdrift makes
both failure modes loud:

- **`envdrift check`** fails CI when `.env.example` and the real environment
  disagree, with a precise, line-numbered report.
- **`envdrift example`** generates example files with every value stripped,
  so there is nothing to leak.
- **`envdrift lint --example`** catches secret-looking values that made it
  into a committed example anyway.
- **`envdrift diff`** answers "what is different between my env and yours?"
  without printing either side's secrets.

## Install

```sh
pipx install git+https://github.com/menno420/codetool-lab-fable5
# or
pip install git+https://github.com/menno420/codetool-lab-fable5
```

No runtime dependencies; requires Python 3.9 or newer.

## Quickstart

```console
$ envdrift check                     # compares .env against .env.example
missing: STRIPE_WEBHOOK_SECRET (in .env.example but not in .env)
drift: 1 missing, 0 extra, 0 empty
$ echo $?
1
```

Fix the drift, and:

```console
$ envdrift check
ok: .env matches .env.example
```

## Commands

### `envdrift check [--env .env] [--example .env.example] [--allow-extra] [--format text|json]`

Compares an env file against its example and reports three kinds of drift:

- **missing** — keys in the example but absent from the env file;
- **extra** — keys in the env file but absent from the example (suppress
  with `--allow-extra`);
- **empty** — keys present in the env file with an *empty* value where the
  example's value is *non-empty*. Heuristic: a non-empty example value marks
  the key as "requires a real value", so an empty env value is reported as
  required-but-empty. Keys whose example value is empty are never reported
  this way.

```console
$ envdrift check --env .env --example .env.example
missing: REDIS_URL (in .env.example but not in .env)
extra: DEBUG_HACK (in .env but not in .env.example)
empty: API_KEY (empty in .env but non-empty in .env.example)
drift: 1 missing, 1 extra, 1 empty
```

### `envdrift diff A B [--values] [--format text|json]`

Key-level diff between two env files: **added** (in B, not A), **removed**
(in A, not B), **changed** (both, different values). Values are hidden by
default so you can safely paste the output into an issue; `--values`
reveals them.

```console
$ envdrift diff .env production.env
+ SENTRY_DSN
- LOCAL_ONLY_FLAG
~ DATABASE_URL: <changed>
$ envdrift diff .env production.env --values
+ SENTRY_DSN=https://abc@sentry.example/1
- LOCAL_ONLY_FLAG=1
~ DATABASE_URL: 'postgres://localhost/dev' -> 'postgres://db.prod/live'
```

### `envdrift example ENVFILE [-o OUT] [--keep-values-for REGEX]`

Generates an example file from a real env file, preserving key order,
comments (standalone and inline), blank lines, and `export ` prefixes —
and stripping **every** value to empty. envdrift deliberately does not try
to guess which values are "safe" to keep; guessing wrong leaks a secret.
If some keys are genuinely harmless (ports, log levels), opt them in
explicitly with `--keep-values-for`:

```console
$ envdrift example .env --keep-values-for '^(PORT|LOG_LEVEL)$'
# Database settings
DB_HOST=
DB_PASSWORD=

# Web
export PORT=8080 # dev port
LOG_LEVEL=info
```

Writes to stdout by default; `-o .env.example` writes a file.

### `envdrift lint FILE [--example] [--format text|json]`

Reports common dotenv mistakes, each with a line number and a stable code:

| code | meaning |
|---|---|
| `duplicate-key` | key assigned more than once (last wins at load time) |
| `invalid-key` | key does not match `[A-Za-z_][A-Za-z0-9_]*` |
| `invalid-line` | line is not blank, comment, or `KEY=value` |
| `space-around-equals` | whitespace around `=` (many loaders misread this) |
| `unclosed-quote` | quoted value never closed |
| `trailing-junk` | unexpected text after a closing quote |
| `secret-key` | `--example` only: secret-sounding key with a non-empty value |
| `high-entropy-value` | `--example` only: value looks like a real credential |

Secret heuristics (only with `--example`, for files meant to be committed):
a key matching `(?i)(secret|token|password|passwd|api_?key|private)` with a
non-empty value, or a value of 20+ base64/hex characters containing both
letters and digits.

```console
$ envdrift lint .env.example --example
.env.example:4: secret-key: AWS_SECRET_ACCESS_KEY looks like a secret but has a non-empty value in an example file
1 finding(s)
```

### Global

```console
$ envdrift --version
envdrift 0.1.0
$ envdrift check --help
```

## Exit codes

| code | meaning |
|---|---|
| 0 | clean — no drift / identical / no findings |
| 1 | findings — drift detected, files differ, or lint findings |
| 2 | error — bad usage, unreadable file, invalid regex |

All error messages go to stderr; reports go to stdout.

## JSON output

Every reporting command accepts `--format json` and emits a single stable
object on stdout:

```jsonc
// envdrift check --format json
{
  "command": "check",
  "env": ".env",
  "example": ".env.example",
  "ok": false,
  "missing": ["REDIS_URL"],   // key names, example order
  "extra": ["DEBUG_HACK"],
  "empty": ["API_KEY"]
}

// envdrift diff A B --format json
{
  "command": "diff",
  "a": ".env",
  "b": "production.env",
  "ok": false,
  "added":   [{"key": "SENTRY_DSN"}],       // + "value" with --values
  "removed": [{"key": "LOCAL_ONLY_FLAG"}],  // + "value" with --values
  "changed": [{"key": "DATABASE_URL"}]      // + "old"/"new" with --values
}

// envdrift lint FILE --format json
{
  "command": "lint",
  "file": ".env.example",
  "ok": false,
  "findings": [
    {"line": 4, "code": "secret-key", "key": "AWS_SECRET_ACCESS_KEY", "message": "..."}
  ]
}
```

`ok` is always present; exit codes are unchanged by `--format json`.

## CI recipe

Gate pull requests on env-file honesty:

```yaml
# .github/workflows/envcheck.yml
name: env check
on: [pull_request]
jobs:
  envdrift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install git+https://github.com/menno420/codetool-lab-fable5
      # example files must be committed and secret-free
      - run: envdrift lint .env.example --example
      # optional: your deploy tooling can render the real env and check it
      # - run: envdrift check --env .env.rendered --example .env.example
```

## Supported dotenv dialect

envdrift parses the common dotenv dialect:

- blank lines and `#` comments (standalone and inline);
- `KEY=value` and `export KEY=value`;
- unquoted, single-quoted, and double-quoted values;
- double-quoted values process `\n`, `\t`, `\\`, `\"` (unknown escapes are
  kept literally); single-quoted values are literal;
- unquoted values may contain `=`; an inline `#` comment is only recognized
  when preceded by whitespace (`COLOR=#ff00aa` is a value);
- empty values (`KEY=`) and whitespace around `=` are parsed (the latter is
  flagged by `lint`);
- on duplicate keys, the last assignment wins (and `lint` reports it).

Deliberately **not** supported: multi-line values, variable interpolation
(`${VAR}`), backslash line continuations, and YAML-ish `KEY: value` syntax.
Files using those features will produce `invalid-line` findings rather than
silent misreads.

## Development

```sh
git clone https://github.com/menno420/codetool-lab-fable5
cd codetool-lab-fable5
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest        # test suite
ruff check .  # lint
```

CI runs both on Python 3.9 through 3.13.

## License

[MIT](LICENSE) © 2026 menno420
