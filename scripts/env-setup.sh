#!/usr/bin/env bash
# Repo-specific dev setup for envdrift (called by environments/setup-universal.sh).
# Same contract: best-effort, never fatal to the caller.
set +e
echo "[envdrift-setup] installing dev environment (editable + test/lint/build tools)"
python3 -m pip install --quiet -e . pytest ruff build \
  || echo "[envdrift-setup] pip install failed (non-fatal — session can self-repair)"
echo "[envdrift-setup] done"
exit 0
