from __future__ import annotations

import subprocess
from typing import Any

VRAM_TARGET_GB = 14.0
VRAM_HARD_LIMIT_GB = 15.2


def gpu_vram_gb() -> tuple[float | None, float | None]:
    try:
        out = subprocess.check_output([
            "nvidia-smi",
            "--query-gpu=memory.used,memory.total",
            "--format=csv,noheader,nounits",
        ], text=True, stderr=subprocess.DEVNULL).strip().splitlines()[0]
        used_mb, total_mb = [float(x.strip()) for x in out.split(",")]
        return used_mb / 1024.0, total_mb / 1024.0
    except Exception:
        return None, None


def status() -> dict[str, Any]:
    used, total = gpu_vram_gb()
    if used is None or total is None:
        return {
            "available": False,
            "used_gb": None,
            "total_gb": None,
            "target_gb": VRAM_TARGET_GB,
            "hard_limit_gb": VRAM_HARD_LIMIT_GB,
            "ok": False,
            "critical": False,
            "reason": "nvidia_smi_unavailable",
        }
    return {
        "available": True,
        "used_gb": round(used, 2),
        "total_gb": round(total, 2),
        "target_gb": VRAM_TARGET_GB,
        "hard_limit_gb": VRAM_HARD_LIMIT_GB,
        "ok": used < VRAM_TARGET_GB,
        "critical": used >= VRAM_HARD_LIMIT_GB,
    }


def assert_safe_for(worker: str) -> None:
    current = status()
    if not current["available"]:
        raise RuntimeError(f"vram_unavailable_for_{worker}")
    if current["critical"]:
        raise RuntimeError(f"vram_hard_limit_reached_for_{worker}")


def text_tokens(worker: str, requested: int) -> int:
    current = status()
    if current.get("critical"):
        return min(requested, 384)
    if current.get("available") and not current.get("ok"):
        return min(requested, 512)
    if worker == "qwen":
        return min(requested, 1024)
    return min(requested, 1024)


def image_params() -> dict[str, int | float]:
    current = status()
    if current.get("critical"):
        return {"width": 384, "height": 384, "steps": 14, "guidance_scale": 7.0}
    if current.get("available") and not current.get("ok"):
        return {"width": 448, "height": 448, "steps": 16, "guidance_scale": 7.0}
    return {"width": 512, "height": 512, "steps": 20, "guidance_scale": 7.0}
