# codetool-lab-fable5 · status
updated: 2026-07-09T14:58Z
phase: shipped
health: green
last-shipped: envdrift 0.1.0 — PR #2 squash-merged to main (73ef38d); tag v0.1.0 NOT pushed (see below)
blockers: none for the code; tag/release creation blocked by session policy
orders: acked=001 done=001
⚑ needs-owner: (1) create tag v0.1.0 at 73ef38d and a GitHub Release "envdrift 0.1.0" — this session's
proxy returns 403 "Creating, editing, or deleting releases is not permitted for this session type"
for both git tag pushes and the releases/refs API, so an owner (or a session with release rights)
must run `git tag v0.1.0 73ef38d && git push origin v0.1.0` and publish a release with the CHANGELOG
0.1.0 body plus dist/ artifacts (`python -m build` reproduces them). (2) PyPI publication needs owner
PyPI credentials — until then install is `pipx install git+https://github.com/menno420/codetool-lab-fable5`.
notes: friction: the GitHub write proxy is finely scoped — branch pushes and PR merges work, but tag
pushes and the releases API are policy-blocked, discovered only by trying. delight: the stranger test
was flawless — fresh venv + pip/pipx install from git, and every README example (check/diff/example/
lint, JSON output, exit codes) reproduced byte-for-byte with zero fixes needed.
