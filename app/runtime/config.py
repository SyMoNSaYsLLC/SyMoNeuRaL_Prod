from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "data" / "runtime"
OUTPUT = ROOT / "data" / "output"

RUNTIME.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)


def _path_from_env(name: str, default: str) -> Path:
    return Path(os.environ.get(name, str(ROOT / default))).expanduser().resolve()


@dataclass(frozen=True)
class ModelPaths:
    gemma: Path = _path_from_env("SYMON_GEMMA_MODEL", "models/llm/gemma")
    qwen: Path = _path_from_env("SYMON_QWEN_MODEL", "models/llm/qwen")
    stable: Path = _path_from_env("SYMON_STABLE_MODEL", "models/sd/v1-5-pruned-emaonly.safetensors")


@dataclass(frozen=True)
class RuntimeSettings:
    device: str = os.environ.get("SYMON_DEVICE", "cuda")
    load_in_4bit: bool = os.environ.get("SYMON_LOAD_4BIT", "0") == "1"
    max_new_tokens_default: int = int(os.environ.get("SYMON_MAX_NEW_TOKENS", "768"))
    image_width: int = int(os.environ.get("SYMON_IMAGE_WIDTH", "512"))
    image_height: int = int(os.environ.get("SYMON_IMAGE_HEIGHT", "512"))
    image_steps: int = int(os.environ.get("SYMON_IMAGE_STEPS", "20"))
    image_guidance: float = float(os.environ.get("SYMON_IMAGE_GUIDANCE", "7.0"))


MODELS = ModelPaths()
SETTINGS = RuntimeSettings()
