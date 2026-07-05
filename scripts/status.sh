#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "===== symoneural manager ====="
PID="$(cat data/runtime/symon-manager.pid 2>/dev/null || true)"
if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
  echo "running pid=$PID"
else
  echo "not running"
fi

echo
echo "===== public port ====="
ss -ltnp | grep ':8000' || echo "8000 not listening"

echo
echo "===== compile ====="
"$ROOT/.venv/bin/python" -m py_compile app/main.py app/symoneural.py app/workers/*.py app/comms/*.py app/runtime/*.py

echo
echo "===== native readiness ====="
"$ROOT/.venv/bin/python" - <<'PY'
from app import symoneural
from app.workers import vram_guard
print({"workers": symoneural.worker_readiness(), "vram": vram_guard.status()})
PY
