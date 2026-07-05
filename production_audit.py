from pathlib import Path
import ast
import sys

ROOT = Path.cwd()
FORBIDDEN = [
    "llama", "llama.cpp", "http://", "https://", "localhost",
    "18080", "18081", "18082", "symon-llm-server", "llama-server",
]
REQUIRED = [
    "app/main.py", "app/symoneural.py", "app/workers/gemma.py", "app/workers/qwen.py",
    "app/workers/safetensor.py", "app/workers/vram_guard.py", "app/runtime/native_text.py",
    "app/runtime/native_image.py", "app/runtime/config.py", "app/runtime/worker_types.py",
    "app/comms/gemmacodercomms.py", "app/comms/gemmaimagingcomms.py", "scripts/start.sh",
    "scripts/stop.sh", "scripts/status.sh", "scripts/test.sh", "README.md", "requirements.txt",
]
checks = []


def check(name: str, ok: bool, detail: str = "") -> None:
    checks.append((name, ok, detail))


for rel in REQUIRED:
    check(f"exists {rel}", (ROOT / rel).exists())

for py in (ROOT / "app").rglob("*.py"):
    if "__pycache__" in py.parts:
        continue
    try:
        ast.parse(py.read_text(), filename=str(py))
        check(f"syntax {py.relative_to(ROOT)}", True)
    except SyntaxError as exc:
        check(f"syntax {py.relative_to(ROOT)}", False, f"{exc.lineno}:{exc.offset} {exc.msg}")

hits = []
for base in [ROOT / "app", ROOT / "scripts"]:
    for path in base.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        text = path.read_text(errors="ignore")
        for token in FORBIDDEN:
            if token in text:
                hits.append(f"{path.relative_to(ROOT)} contains {token}")
check("no forbidden old runtime/url tokens", not hits, "; ".join(hits[:20]))

for rel in ["app/workers/gemma.py", "app/workers/qwen.py", "app/workers/safetensor.py"]:
    text = (ROOT / rel).read_text()
    check(f"{rel} has native implementation", "NotImplementedError" not in text and "native_" in text)

readme = (ROOT / "README.md").read_text()
check("README states production wiring", "Production-ready native Python worker wiring" in readme)
check("README documents env model paths", "SYMON_GEMMA_MODEL" in readme and "SYMON_QWEN_MODEL" in readme and "SYMON_STABLE_MODEL" in readme)

failed = 0
print("SyMoNeuRaL production audit")
print("=" * 32)
for name, ok, detail in checks:
    print(f"{'PASS' if ok else 'FAIL':4}  {name}" + (f" -> {detail}" if detail else ""))
    failed += 0 if ok else 1
print("=" * 32)
print(f"Total: {len(checks)} checks | Failed: {failed}")
sys.exit(1 if failed else 0)
