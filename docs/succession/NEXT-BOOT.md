# NEXT BOOT — first 10 minutes for the gen-2 session

You are the fresh incarnation of the codetool-lab-fable5 lane. Chat context did not survive; everything you need is committed. Do these in order.

## 0. Heartbeat before work (minute 0–2)
Your FIRST act: land a one-line liveness signal (status.md `updated:` bump or a WIP commit) via the fastest allowed path. A silent session is indistinguishable from a dead one; your predecessor was invisible for 76 minutes once. If the platform lets you do nothing else, that fact itself is the ⚑ to surface.

## 1. Read order (minute 2–6)
1. `control/inbox.md` — the mission. Orders stay `status: new` in the file forever (the manager flips them rarely); diff order IDs against status.md's `acked=/done=` to find YOUR queue.
2. `control/status.md` — where gen-1 stopped: wind-down marker, ⚑ owner items outstanding.
3. `control/README.md` — bus protocol; one writer per file; inbox is never yours to edit.
4. `docs/succession/PLATFORM-LIMITS.md` — every known wall WITH exact error text. Probing a documented wall twice is a bug.
5. `docs/ROADMAP.md` — done / in-flight / next; 0.3.0 candidates in priority order.
6. `docs/succession/custom-instructions-proposal.md` — the conventions gen-1 wants you born with (READY-never-draft, merge-on-green directly, heartbeat batching, decide-and-flag).
7. `README.md` + `CHANGELOG.md` — the product you now own (envdrift 0.2.0, zero-dependency, exit-code contract documented).
8. Optional depth later: `docs/retro/` (whole-life review, ORDER 003 self-review by question ID).

## 2. Walking skeleton (minute 6–10, BEFORE real work)
Prove branch → PR → CI → merge end-to-end: branch `skeleton/boot-<date>`; add `docs/boot-checks/<date>.md` ("boot check <timestamp>"); open a READY PR; watch CI actually run and go green; merge on green. If ANY link fails, that failure — with exact text — is your first status ⚑, ahead of all product work. Batch your §0 heartbeat into this PR if you didn't land it already.

## 3. Then work
Top of ROADMAP.md "Next", or any new inbox order first (P0 pings before everything — see ORDER 004's shape). Verification bar you inherit: fresh-venv + pipx install from git, byte-exact README replay, before merging anything user-facing. One status heartbeat per session, batched into your substantive PR.

## Environment facts you need
- Dev env: `environments/setup-universal.sh` is the environment's setup script (defensive, always exits 0); it routes through `scripts/env-setup.sh` which installs the dev tools (pytest, ruff, build) and the package editable.
- Env var names required by this lane: **none.** The tool is zero-dependency and needs no secrets. (PyPI, if ever granted, arrives via Trusted Publishing — also no committed secrets.)
- GitHub: use the MCP tools, not shell (`gh` absent; raw api.github.com blocked — exact texts in PLATFORM-LIMITS.md).
