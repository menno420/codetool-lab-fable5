# Environment spec — gen-2 boot (codetool-lab-fable5 lane)

## Setup script (TESTED)
Use `environments/setup-universal.sh` (adopted verbatim from fleet-manager `environments/templates/setup-universal.sh`, canonical copy there) as the environment's setup script. Contract: defensive, shape-agnostic, ALWAYS exits 0 — a failing setup script is a dead session with no signal (gen-1's 76-minute case).

Repo-side hook: `scripts/env-setup.sh` (detected and run by the universal script; single source of truth for this repo's dev deps).

Test evidence (run at wind-down, 2026-07-09T20:02Z):
- Single-repo mode (run inside a fresh clone of this repo, before the hook existed): detected the repo, logged `no scripts/env-setup.sh or requirements.txt — skipping`, exit code 0.
- Empty-dir mode (run in a fresh empty directory): logged the skip path, exit code 0.
- Routing test (run inside the clone after adding `scripts/env-setup.sh`): universal script detected and ran the hook (`repo: running scripts/env-setup.sh` → `[envdrift-setup] installing dev environment` → `[envdrift-setup] done`), pip install of `-e . pytest ruff build` succeeded (no network errors; only pip's root-user warning), exit code 0.
- Resulting dev env verified: `python3 -m pytest -q` in the clone → **111 passed**, exit code 0.

## Environment variables
Required by this lane: **none** — envdrift is zero-dependency and handles no secrets. Do not add credentials to the environment for this lane. If PyPI Trusted Publishing is ever configured (owner action), it uses OIDC — still no stored secrets. Names-only policy: this file never contains values.
