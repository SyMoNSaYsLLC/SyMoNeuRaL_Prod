#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
"$ROOT/.venv/bin/python" - <<'PY'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
health = client.get('/health')
assert health.status_code == 200, health.text
models = client.get('/v1/models')
assert models.status_code == 200, models.text
print('health:', health.json())
print('models:', models.json())
PY
