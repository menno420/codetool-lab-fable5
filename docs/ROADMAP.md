# envdrift · roadmap & queue state (wind-down snapshot, 2026-07-09)

Queue state at gen-1 wind-down. Nothing dangling: **zero open PRs, zero branches besides main** (verified at wind-down).

## Done
- 0.1.0 — check/diff/example/lint CLI, 66 tests, CI py3.9–3.13 (PR #2, `73ef38d`)
- Gen-1 retro: project review + ORDER 003 self-review (PR #7, `1b4f5da`); status heartbeats (PRs #4, #5, #8)
- 0.2.0 — sync, check --fix, pre-commit/Actions recipes, parser hardening: multiline quotes, BOM, CRLF (PR #9, `13a84e5`), 111 tests
- ORDER 004 ping-ack (PR #11)
- Wind-down succession pack (this PR)

## In flight
- None. All work merged; builder session idle at wind-down.

## Next (0.3.0 candidates — unstarted, priority order)
1. Typed constraints in example files (`# envdrift: required,int` comment annotations) → `check` validates types/requiredness — turns the example file into a lightweight schema.
2. Multi-env comparison: `envdrift check --against staging.env prod.env` (drift across deploy targets, not just local vs example).
3. `lint --fix` (auto-remove duplicates, normalize quoting) with `--dry-run`.
4. Real-world corpus expansion for the parser (A3 check from the self-review): harvest popular OSS `.env.example` files, diff acceptance vs python-dotenv.
5. Shell completion (argparse-native) + man page.

## Parked / debt
- Bare `KEY` lines (no `=`): documented-unsupported since 0.2.0 — revisit only with corpus evidence.
- Windows runner absent from CI matrix (POSIX-only tested; CRLF handled at parser level).
- Tag/Release/PyPI: ⚑ owner-only (policy wall — see docs/succession/PLATFORM-LIMITS.md).
- Release automation via Actions: policy-denied in this lane; do not re-attempt without a platform-level grant.
