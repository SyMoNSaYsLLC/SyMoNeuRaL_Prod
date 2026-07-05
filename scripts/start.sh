#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p data/runtime data/output

if [ ! -x "$ROOT/.venv/bin/python" ]; then
  echo "ERROR: missing .venv python. Create it and install requirements.txt first."
  exit 1
fi

source "$ROOT/.venv/bin/activate"

PID="$(cat data/runtime/symon-manager.pid 2>/dev/null || true)"
if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
  kill "$PID" 2>/dev/null || true
fi

nohup "$ROOT/.venv/bin/python" -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  > data/runtime/symon-manager.log 2>&1 &

echo "$!" > data/runtime/symon-manager.pid
echo "SyMoNeuRaL public manager started on port 8000"
