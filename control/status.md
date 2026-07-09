# codetool-lab-fable5 · status
updated: 2026-07-09T17:21Z
phase: shipped-0.2.0
health: green
last-shipped: envdrift 0.2.0 — sync command + check --fix + parser hardening (multi-line quoted
values, BOM, CRLF corpus); PR #9
blockers: none
orders: acked=001,002,003 done=001,002,003
⚑ needs-owner: tag v0.2.0 + GitHub Release + PyPI (same ritual as v0.1.0 — steps in
docs/retro/project-review-2026-07-09.md §(e); agents remain policy-blocked on tags/releases).
notes: friction/delight — delight: the 0.1.0 parser's lossless line model made multi-line/BOM/CRLF
hardening almost mechanical, and the whole 0.2.0 suite (111 tests) passed first try in the
stranger-install replay; no real friction this session.
