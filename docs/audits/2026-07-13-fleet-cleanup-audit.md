# codetool-lab-fable5 — fleet cleanup audit (2026-07-13)

> Complementary cleanup/audit pass during the fleet-wide EAP wind-down (owner ORDER 045,
> issued live to the fleet-manager coordinator ~2026-07-13T22:00–22:30Z). This session did
> not dispatch new work and did not touch `control/inbox.md` (manager-owned) or any other
> repo's control bus. Read-only audit + this report only.

## What this repo is

`envdrift` — a zero-dependency Python CLI/library that detects drift between a real `.env`
file and its committed `.env.example`, diffs env files across machines/environments,
generates safe example files, and lints for common dotenv mistakes (duplicate keys,
unclosed quotes, secret-looking values in example files, etc.). Python 3.9+, standard
library only, shipped as `envdrift` on PyPI-style install (`pip install git+…`, PyPI
publish itself still pending — see Findings). Source lives under `src/envdrift/`
(`cli.py`, `parser.py`, `commands/{check,diff,example,lint,sync}.py`); 111 tests in
`tests/`.

Distinct from the product, `control/` is fleet-coordination metadata (inbox/status/README)
used by a `menno420/*`-fleet manager to dispatch orders and read heartbeats from this lane
— explicitly called out as unrelated to the envdrift package in the README (line 10-12).

## Structure

```
src/envdrift/            # package: cli.py, parser.py, commands/{check,diff,example,lint,sync}.py
tests/                   # 8 test files, 111 tests (pytest)
docs/
  ROADMAP.md             # wind-down snapshot: done / in-flight / 0.3.0 candidates / parked
  retro/                 # QUESTIONS.md, project-review, self-review, wind-down-review, ping-ack
  succession/            # NEXT-BOOT, PLATFORM-LIMITS, ENVIRONMENT, gen2-feedback, custom-instructions-proposal
control/                 # inbox.md (manager-written), status.md (this lane's heartbeat), README.md (bus protocol)
environments/            # setup-universal.sh (defensive, always-exit-0 fleet shim)
scripts/                 # env-setup.sh (repo-specific dev install, called by the shim)
.github/workflows/ci.yml # matrix CI (py3.9–3.13): ruff + pytest
pyproject.toml           # hatchling build, version 0.2.0
CHANGELOG.md             # Keep a Changelog format, 0.1.0 and 0.2.0 entries
LICENSE                  # MIT, 2026 menno420
```

## CI setup and health

`.github/workflows/ci.yml` runs on `pull_request` → `main` and on `push` to `feat/**`, a
5-way matrix (Python 3.9–3.13), each job: `pip install -e '.[dev]'` → `ruff check .` →
`pytest`. Checked live via `mcp__github__actions_list` (`list_workflow_runs`, `ci.yml`):
**every run for this repo is `completed` / `conclusion: success`** — 15/15 most-recent runs
green, most recently run `29091546674` on PR #14 (`fix/release-wall-correction`,
2026-07-10T12:07:15Z).

Independently re-verified locally (not just trusting the CI badge, per the "green check
vs. visible evidence" rule): built a fresh `python3.10` venv, `pip install -e '.[dev]'`,
then `pytest -q` → **111 passed**, and `ruff check .` → **All checks passed**. No
discrepancy between the live CI history and a from-scratch local run.

CI matrix caveat already self-documented in `docs/ROADMAP.md` line 24: **no Windows
runner** — the tool is tested POSIX-only; CRLF handling is exercised at the parser level
via fixtures, not via an actual Windows CI job. Flagged there as a known/accepted gap, not
new.

## Open PRs

**Zero open PRs.** `mcp__github__list_pull_requests` (state=open) returned `[]`. Only one
branch exists on the remote: `main` (protected) — `mcp__github__list_branches` returned a
single entry, matching the local clone's `git branch -a`. This matches the repo's own
`docs/ROADMAP.md` line 3 claim ("zero open PRs, zero branches besides main — verified at
wind-down") and `control/status.md`'s `phase: wind-down complete`. Nothing to merge, close,
or flag under the safety rules — there was no PR-disposition work to do in this repo.

Last commit to `main`: `a6cf1a9` (PR #14, "Succession-doc fix: release-wall is
SEAT-DEPENDENT, not 'route closed'"), merged 2026-07-10T12:07:20Z — roughly 3 days before
this audit, well outside the "last 2-3 hours = live work" caution window. Combined with
`control/status.md`'s explicit `phase: wind-down complete — ready for archive + fresh
session` and `blockers: none`, this repo reads as genuinely dormant, not merely quiet.

## Doc quality

Notably strong for a small tool repo. The succession pack
(`docs/succession/{NEXT-BOOT,PLATFORM-LIMITS,ENVIRONMENT,gen2-feedback,
custom-instructions-proposal}.md`) and retro set (`docs/retro/{QUESTIONS,
project-review-2026-07-09,self-review-2026-07-09,wind-down-review-2026-07-09,
ping-ack}.md`) are unusually thorough: every platform wall in `PLATFORM-LIMITS.md` is
recorded with the literal error text, a verdict, and (for item 4, the release-workflow
wall) a **dated correction rider** showing the fleet already caught and fixed an
over-generalized claim ("route closed" → "seat-dependent") by cross-checking against a
sibling lane (`codetool-lab-opus4.8`) that proved the route works from a different seat.
That correction is itself a good model of the "green check vs. evidence" discipline this
audit was asked to apply.

README.md is complete and accurate against the shipped code: version banner (`envdrift
0.2.0`), the exit-code table, and every documented subcommand (`check`, `sync`, `diff`,
`example`, `lint`) match `src/envdrift/commands/` 1:1. CHANGELOG.md correctly tracks
`pyproject.toml`'s version (both `0.2.0`).

## Findings — inconsistencies / errors

1. **Compiled bytecode is committed to git; no `.gitignore` exists.** `git ls-files | grep
   pycache` returns 11 tracked files: `src/envdrift/commands/__pycache__/*.cpython-311.pyc`
   (5 files) and `tests/__pycache__/*.cpython-311-pytest-9.1.1.pyc` (6 files). There is no
   `.gitignore` anywhere in the repo (`ls -la` at root shows none). This is build noise —
   harmless to the tool's behavior — but it's dead weight in every clone/diff and a minor
   embarrassment for a "stranger installs and it just works" pitch. Not fixed in this pass
   (audit-only scope per this session's instructions); flagged for whoever next touches
   this repo, including the archive step.
2. **Pending owner-only items are still open, per the repo's own tracking.**
   `control/status.md` lists three `⚑ needs-owner` items that remain outstanding as of the
   last heartbeat (2026-07-09T20:06Z, unchanged since): (1) tag `v0.1.0`
   (`73ef38d`) + `v0.2.0` (`13a84e5`) + GitHub Releases — agents in this lane hit hard
   403 walls on tag-push and the Releases API (`docs/succession/PLATFORM-LIMITS.md` items
   1–3); (2) PyPI publish (optional, needs owner creds or Trusted Publishing); (3) the
   gen-2 boot handoff itself, which per this audit's brief is superseded by the archive
   decision rather than a fresh session. Not an inconsistency in the repo's own bookkeeping
   — it accurately reports these as unresolved — but worth surfacing since they're easy to
   miss once the repo is archived and no longer generates heartbeats.
3. **No functional or documentation defects found.** README claims were spot-checked
   against `src/envdrift/commands/*.py` behavior (exit codes, `sync` append semantics,
   `--fix` scope) and against the test suite; nothing contradicted the docs. This is a
   clean, small, well-tested tool at the point it was frozen.

## What was done this session

Read-only audit only, as instructed: no PR disposition needed (none existed), no code
changes, no `control/` writes (inbox is manager-owned; status.md is this lane's own
heartbeat file and was left untouched since this session is explicitly *not* a builder
wake — writing a new status heartbeat here would misrepresent this as an active lane
resuming work, which it is not). This report is the only artifact produced.

## Suggestions

1. **Fleet-wide `.gitignore` template.** At least this repo ships with zero `.gitignore`
   and 11 committed `.pyc` files. If other `codetool-lab-*` lanes were seeded from the same
   pattern, a one-time sweep (or a template added to whatever seeds new lanes, e.g. the
   `fleet-manager` `environments/templates/` area referenced in
   `environments/setup-universal.sh`) would prevent recurrence fleet-wide rather than
   per-repo.
2. **Centralize `PLATFORM-LIMITS.md` truly fleet-wide, not lane-by-lane copies.** This
   repo's copy already documents that it caught and corrected a stale claim by
   cross-referencing a sibling lane's live evidence (item 4's correction rider). That
   cross-lane reconciliation is valuable but currently happens by manual, per-repo edit;
   a single fleet-owned source (already gestured at — `docs/succession/PLATFORM-LIMITS.md`
   says "Ship PLATFORM-LIMITS.md pre-filled at seed" in `gen2-feedback.md` item 3) would
   stop the union-of-walls knowledge from silently forking across ~20 repos.
3. **Archive-readiness checklist could be codified.** This repo's own `status.md` +
   `ROADMAP.md` pair already demonstrates what "verified ready for archive" looks like
   (zero open PRs, zero stray branches, all `⚑ needs-owner` items enumerated, CI green,
   succession docs complete) — that's a good candidate for a small reusable checklist
   (fleet-manager side) other lanes' wind-downs can be graded against before the owner
   commits to archiving them, rather than each lane inventing its own wind-down review
   format from scratch (compare this repo's `docs/retro/wind-down-review-2026-07-09.md`
   against whatever ad hoc form other lanes may have used).
4. **Risk: the two owner-only items (tags/Releases, PyPI) will be easy to lose track of
   post-archive.** If `codetool-lab-fable5` is archived per the queued consolidation
   decision, `control/status.md`'s `⚑ needs-owner` lines stop being visible to the fleet
   heartbeat scan (`fleet_status.py`-style tooling, per the sibling `superbot` repo's
   convention) once the repo is no longer polled. Worth a one-line note in whatever
   consolidation/archive record captures this repo's disposition, so "tag v0.1.0/v0.2.0 +
   release the two versions" doesn't silently disappear.

## Evidence index

- No open PRs: `mcp__github__list_pull_requests(state=open)` → `[]` (checked 2026-07-13).
- Single branch `main`: `mcp__github__list_branches` → `[{"name":"main","sha":"a6cf1a9…",
  "protected":true}]`.
- CI history: `mcp__github__actions_list(list_workflow_runs, ci.yml)` — 15 most recent runs,
  all `completed`/`success`; most recent `29091546674` (PR #14, 2026-07-10T12:07:15Z).
- Local re-verification: `python3.10 -m venv` + `pip install -e '.[dev]'` + `pytest -q` →
  `111 passed`; `ruff check .` → `All checks passed!` (run 2026-07-13).
- Tracked bytecode: `git ls-files | grep pycache` → 11 files (5 under
  `src/envdrift/commands/__pycache__/`, 6 under `tests/__pycache__/`); no `.gitignore` in
  repo root.
- Last commit: `a6cf1a9d5e8b1082025e8a4c9abce9febd2aea92`, PR #14, merged
  2026-07-10T12:07:20Z.
- Status/roadmap self-report: `control/status.md` (`phase: wind-down complete — ready for
  archive + fresh session`, `blockers: none`), `docs/ROADMAP.md` line 3.
