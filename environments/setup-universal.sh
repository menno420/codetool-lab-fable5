#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup-universal.sh — the fleet's universal defensive setup shim
#
# Canonical copy: menno420/fleet-manager · environments/templates/setup-universal.sh
# Owner pastes this into: claude.ai/code → Environments → <env> → Setup script.
#
# CONTRACT (fleet playbook R15): this script NEVER fails the session.
# A failing setup script = dead session, no signal — the worker never even
# reports. Every step below is non-fatal and the script ALWAYS exits 0.
# Worst case is a session with missing deps that can still report and
# self-repair; that beats no session at all.
# ---------------------------------------------------------------------------

# --- Block 1: defensive posture --------------------------------------------
# set +e     -> a non-zero step must not abort the script.
# no set -u  -> unset variables are tolerated, never fatal.
# no pipefail-> a hiccup mid-pipe is tolerated, never fatal.
set +e

log() { echo "[env-setup] $*"; }

# --- Block 2: per-repo setup ------------------------------------------------
# Detection order for each repo, most-specific first:
#   1. repo ships scripts/env-setup.sh  -> run it (the repo knows best; this is
#      also the escape hatch for repos pinned to a non-default interpreter,
#      e.g. superbot's python3.10 CI parity — bare python3 here may be 3.11).
#   2. repo has requirements.txt        -> pip install it under python3.
#   3. neither                          -> skip silently (docs-only repo is fine).
# Every branch is guarded: one broken repo must never block the others.
setup_one() {
  repo_dir="$1"
  name="$(basename "$repo_dir")"
  if [ -f "$repo_dir/scripts/env-setup.sh" ]; then
    log "$name: running scripts/env-setup.sh"
    ( cd "$repo_dir" && bash scripts/env-setup.sh ) \
      || log "$name: env-setup.sh failed (non-fatal, continuing)"
  elif [ -f "$repo_dir/requirements.txt" ]; then
    log "$name: python3 -m pip install -r requirements.txt"
    ( cd "$repo_dir" && python3 -m pip install --quiet -r requirements.txt ) \
      || log "$name: pip install failed (non-fatal, continuing)"
  else
    log "$name: no scripts/env-setup.sh or requirements.txt — skipping"
  fi
}

# --- Block 3: multi-repo vs single-repo detection ---------------------------
# Multi-repo environment: the working dir is a workspace whose CHILD dirs are
# the git clones (e.g. /home/user/{superbot,websites,...}).
# Single-repo environment: the working dir IS the repo (it has .git).
if [ -d .git ]; then
  # Single-repo fallback: set up the repo we are standing in.
  setup_one "$PWD"
else
  found=0
  for d in */; do
    [ -d "$d/.git" ] || continue
    found=1
    setup_one "$PWD/${d%/}"
  done
  # Nothing looked like a git clone: still try the cwd itself, so a bare
  # checkout without .git (or an unexpected layout) gets a best-effort pass.
  [ "$found" -eq 1 ] || setup_one "$PWD"
fi

# --- Block 4: unconditional success ------------------------------------------
# The single most important line in the file (R15). Do not "improve" this.
log "setup complete (defensive shim: always exit 0)"
exit 0
