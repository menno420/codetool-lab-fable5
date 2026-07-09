# codetool-lab-fable5 · status
updated: 2026-07-09T15:01Z
phase: shipped
health: green
last-shipped: envdrift 0.1.0 — PR #2 squash-merged to main (73ef38d); stranger install from main
verified against README (fresh venv + pipx from git, every documented example reproduced).
blockers: none
orders: acked=001,002 done=001,002 — ORDER 002's done-when (commits + a Project-written status.md
landed on main) is satisfied by PRs #2/#4 and this heartbeat; we adopt the standing convention going
forward: READY PRs (never drafts) with auto-merge, and status.md overwritten as the last step of
every session.
⚑ needs-owner:
  (1) tag v0.1.0 + GitHub Release are blocked by this session's GitHub write policy — 403 on both
      tag push and the releases API. Owner can run:
      `git tag v0.1.0 73ef38dad372858d112d04d298923f8b97d62a24 && git push origin v0.1.0`,
      then `python -m build` and create a Release from the tag attaching dist/*.tar.gz + dist/*.whl
      (release body draft prepared; CHANGELOG 0.1.0 entry is the source of truth).
  (2) PyPI publication needs owner credentials — until then install is
      `pipx install git+https://github.com/menno420/codetool-lab-fable5`.
notes: friction: the GitHub write-proxy scope was only discoverable by trying — tag push and the
releases API are blocked while branch push/PR operations work. delight: the stranger README
walkthrough needed zero fixes.
