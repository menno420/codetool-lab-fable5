# Merge-automation verification probe

This file is a merge-automation verification probe created on 2026-07-15.

It is an intentionally inert, content-only change (no `.github/workflows/**`
touched) used to confirm whether ordinary code/doc PRs in this repo land on
green CI with zero human click. See PR #17 (`.github/workflows/merge-on-green.yml`)
for the mechanism this probe is meant to exercise once that workflow file is
merged by the owner.

Safe to delete at any time.
