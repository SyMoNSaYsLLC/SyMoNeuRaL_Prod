from __future__ import annotations

from app.runtime import native_text
from app.runtime.config import MODELS
from app.runtime.worker_types import WorkerResult
from app.workers import vram_guard

NAME = "qwen"
MODEL_NAME = "qwen_coder"


def ready() -> bool:
    return native_text.ready(MODELS.qwen)


def code(task: str, max_tokens: int = 1024) -> WorkerResult:
    vram_guard.assert_safe_for(NAME)
    if not ready():
        raise RuntimeError("qwen_worker_not_ready")
    tokens = vram_guard.text_tokens(NAME, max_tokens)
    content = native_text.generate(
        name=NAME,
        model_path=MODELS.qwen,
        system=(
            "You are SyMoNeuRaL Qwen Coder. Produce exact commands, patches, or complete code. "
            "Preserve filenames and extensions. Be direct and avoid backend commentary."
        ),
        prompt=task,
        max_new_tokens=tokens,
        temperature=0.2,
    )
    return WorkerResult(worker=NAME, content=content)
