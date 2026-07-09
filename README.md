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
- **`envdrift sync`** (and `check --fix`) writes the missing keys into your
  `.env` with the example's values as safe placeholders — no more copying
  them over by hand.
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

Let envdrift fix it, and re-check:

```console
$ envdrift sync
added: STRIPE_WEBHOOK_SECRET
sync: added 1 key(s) to .env
$ envdrift check
ok: .env matches .env.example
```

## Commands

### `envdrift check [--env .env] [--example .env.example] [--allow-extra] [--fix] [--format text|json]`

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

**`--fix`** reports the drift as usual, then appends the *missing* keys to
the env file exactly as `envdrift sync` does (same comment marker, same
placeholder values — see below). Only the missing category is fixable;
`extra` and `empty` findings are reported but never auto-fixed (envdrift
will not delete your keys or invent values). Exit codes with `--fix`:
**0** if everything fixable was fixed and no unfixable drift remains,
**1** if unfixable drift (`extra`/`empty`) remains, **2** on errors.
Unlike `sync`, `check --fix` requires the env file to exist.

```console
$ envdrift check --fix
missing: REDIS_URL (in .env.example but not in .env)
extra: DEBUG_HACK (in .env but not in .env.example)
drift: 1 missing, 1 extra, 0 empty
fixed: added REDIS_URL to .env
fix: added 1 key(s); 1 unfixable finding(s) remain
$ echo $?
1
```

### `envdrift sync [--env .env] [--example .env.example] [--dry-run] [--format text|json]`

Appends every key that is present in the example but missing from the env
file, at the **end** of the env file under a `# added by envdrift sync`
comment, using the example's value **verbatim** as the placeholder —
`.env.example` is non-secret by design, so its values are safe scaffolding
defaults. sync never modifies or overwrites existing keys or values, never
reorders anything, and preserves the existing content byte-for-byte apart
from the appended block (plus a terminating newline if the file lacked
one). If the env file does not exist, it is created. CRLF files get a
CRLF-terminated block.

```console
$ cat .env.example
DB_HOST=localhost
DB_PASSWORD=
REDIS_URL=redis://localhost:6379/0
$ envdrift sync
added: DB_PASSWORD
added: REDIS_URL
sync: added 2 key(s) to .env
$ echo $?
0
```

**`--dry-run`** prints what would be added and writes nothing, with
`check`-style CI-friendly exit codes: **1** if changes would be made,
**0** if already in sync, **2** on errors.

```console
$ envdrift sync --dry-run
would add: DB_PASSWORD (from .env.example)
would add: REDIS_URL (from .env.example)
sync: would add 2 key(s) to .env (dry-run)
$ echo $?
1
```

Without `--dry-run` the exit code is **0** on success (including "nothing
to add") and **2** on errors.

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
envdrift 0.2.0
$ envdrift check --help
```

## Exit codes

| code | meaning |
|---|---|
| 0 | clean — no drift / identical / no findings / write succeeded |
| 1 | findings — drift detected, files differ, lint findings, or changes would be made |
| 2 | error — bad usage, unreadable file, invalid regex |

Per command:

| command | 0 | 1 |
|---|---|---|
| `check` | no drift | drift found |
| `check --fix` | everything fixable fixed, nothing unfixable remains | unfixable drift (`extra`/`empty`) remains |
| `sync` | success (keys appended, or nothing to add) | — (never) |
| `sync --dry-run` | already in sync | changes would be made |
| `diff` | identical | differences |
| `lint` | clean | findings |
| `example` | written | — (never) |

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

// envdrift check --fix --format json adds:
//   "fixed": ["REDIS_URL"]        // keys appended to the env file

// envdrift sync --format json
{
  "command": "sync",
  "env": ".env",
  "example": ".env.example",
  "dry_run": false,
  "ok": true,                 // mirrors the exit code (0 <=> true)
  "added": ["DB_PASSWORD"],   // keys appended (or that would be, with --dry-run)
  "created": false            // true when sync created the env file
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

## Recipes

### pre-commit hook

A [pre-commit](https://pre-commit.com) `repo: local` hook that blocks
commits while your `.env` is out of step with the committed example
(`envdrift check` exits 1 on drift, which fails the hook):

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: envdrift-check
        name: envdrift check
        entry: envdrift check
        language: python
        additional_dependencies:
          - "envdrift @ git+https://github.com/menno420/codetool-lab-fable5"
        pass_filenames: false
        always_run: true
```

When the hook fails, `envdrift sync` (or `envdrift check --fix`) writes
the missing keys for you; fill in the real values and commit again.

### GitHub Actions job

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
      # fail the job if a template .env would need changes (nothing is written)
      # - run: envdrift sync --env .env.defaults --example .env.example --dry-run
      # optional: your deploy tooling can render the real env and check it
      # - run: envdrift check --env .env.rendered --example .env.example
```

## Supported dotenv dialect

envdrift parses the common dotenv dialect:

- blank lines and `#` comments (standalone and inline);
- `KEY=value` and `export KEY=value` (any spacing after `export`);
- unquoted, single-quoted, and double-quoted values;
- double-quoted values process `\n`, `\t`, `\\`, `\"` (unknown escapes are
  kept literally); single-quoted values are literal;
- **multi-line quoted values**: a quoted value that does not close on its
  own line continues across the following lines to the closing quote; line
  breaks inside the value are `\n` regardless of the file's line endings.
  If the quote never closes anywhere in the file, only the first line is
  consumed and `lint` reports `unclosed-quote`;
- `#` inside a quoted value is part of the value, never a comment; an
  unquoted inline `#` comment is only recognized when preceded by
  whitespace (`COLOR=#ff00aa` is a value);
- unquoted values may contain `=`;
- CRLF line endings and a UTF-8 BOM at the start of the file are accepted
  and preserved; values never include a stray `\r`, and the BOM is never
  treated as part of the first key;
- empty values (`KEY=`) and whitespace around `=` are parsed (the latter is
  flagged by `lint`); trailing whitespace after a closing quote is ignored;
- on duplicate keys, the last assignment wins (and `lint` reports it).

Deliberately **not** supported: variable interpolation (`${VAR}`),
backslash line continuations, bare `KEY` with no `=`, and YAML-ish
`KEY: value` syntax. Files using those features will produce
`invalid-line` findings rather than silent misreads.

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
