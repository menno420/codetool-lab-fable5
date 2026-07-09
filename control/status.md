# codetool-lab-fable5 · status
updated: 2026-07-09T17:01Z
phase: gen-1 retro complete; continuing envdrift 0.2.0 (sync, check --fix, recipes, parser corpus hardening)
health: green
last-shipped: #7 — gen-1 retro: project review + ORDER 003 self-review
blockers: none
orders: acked=001,002,003 done=001,002,003
⚑ needs-owner:
  (1) v0.1.0 tag + GitHub Release — exact steps in docs/retro/project-review-2026-07-09.md §(e); agents are policy-blocked (403 + denied workflow route, incl. one owner-authorized attempt).
  (2) PyPI publication — owner credentials or Trusted Publishing setup; steps in the same §(e).
notes: retro honest-take: biggest losses were the dead first boot (seed setup script) and the release
policy wall; the tool itself shipped clean (zero CI fix rounds, byte-exact stranger test). 0.2.0
work proceeds without owner input; heartbeats now batched (max one status PR per session).
