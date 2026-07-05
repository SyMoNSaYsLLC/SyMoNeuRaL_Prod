from __future__ import annotations

from app.runtime import native_text
from app.runtime.config import MODELS
from app.runtime.worker_types import WorkerDecision, WorkerResult
from app.workers import vram_guard

NAME = "gemma"
MODEL_NAME = "gemma_writer_manager"


def ready() -> bool:
    return native_text.ready(MODELS.gemma)


def _heuristic(prompt: str) -> WorkerDecision:
    p = prompt.lower()
    if any(x in p for x in ["draw", "image", "picture", "photo", "render", "safetensor", "stable"]):
        return WorkerDecision(worker="safetensor", task=prompt, check="image_request")
    if any(x in p for x in ["code", "script", "python", "bash", "rust", "cpp", "c++", "debug", "repo", "bitbake", ".bb"]):
        return WorkerDecision(worker="qwen", task=prompt, check="code_request")
    return WorkerDecision(worker="gemma", task=prompt, check="writer_request")


def decide(prompt: str) -> WorkerDecision:
    if not ready():
        return _heuristic(prompt)

    system = (
        "You are SyMoNeuRaL Gemma Manager. Choose exactly one worker name for the request. "
        "Return compact JSON only with keys worker, task, check. "
        "Allowed worker values: gemma, qwen, safetensor. "
        "Use qwen for coding/build/debug/repo tasks. Use safetensor for image generation. "
        "Use gemma for writing, planning, explanation, management, and normal conversation."
    )
    try:
        raw = native_text.generate(
            name=NAME,
            model_path=MODELS.gemma,
            system=system,
            prompt=prompt,
            max_new_tokens=256,
            temperature=0.05,
        )
        obj = native_text.compact_json(raw)
        worker = str(obj.get("worker", "gemma")).strip().lower()
        if worker not in {"gemma", "qwen", "safetensor"}:
            return _heuristic(prompt)
        return WorkerDecision(worker=worker, task=str(obj.get("task") or prompt), check=str(obj.get("check") or "gemma_manager"))
    except Exception:
        return _heuristic(prompt)


def write(prompt: str, max_tokens: int = 768) -> WorkerResult:
    vram_guard.assert_safe_for(NAME)
    if not ready():
        raise RuntimeError("gemma_worker_not_ready")
    tokens = vram_guard.text_tokens(NAME, max_tokens)
    content = native_text.generate(
        name=NAME,
        model_path=MODELS.gemma,
        system="You are SyMoNeuRaL Gemma Writer/Manager. Answer clearly and do not expose backend routing.",
        prompt=prompt,
        max_new_tokens=tokens,
        temperature=0.35,
    )
    return WorkerResult(worker=NAME, content=content)


def final_check(original: str, draft: str) -> WorkerResult:
    if not ready():
        return WorkerResult(worker=NAME, content=draft)
    try:
        checked = native_text.generate(
            name=NAME,
            model_path=MODELS.gemma,
            system="You are SyMoNeuRaL final checker. Return the final user-facing answer only.",
            prompt=f"Original request:\n{original}\n\nDraft answer:\n{draft}",
            max_new_tokens=min(768, max(256, len(draft.split()) * 2)),
            temperature=0.1,
        )
        return WorkerResult(worker=NAME, content=checked or draft)
    except Exception:
        return WorkerResult(worker=NAME, content=draft)
