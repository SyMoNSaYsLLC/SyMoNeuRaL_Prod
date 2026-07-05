from __future__ import annotations

from app.runtime import native_image
from app.runtime.config import MODELS, OUTPUT, SETTINGS
from app.runtime.worker_types import WorkerResult
from app.workers import vram_guard

NAME = "safetensor"
MODEL_NAME = "stable_safetensor"


def ready() -> bool:
    return native_image.ready(MODELS.stable)


def image(prompt: str) -> WorkerResult:
    vram_guard.assert_safe_for(NAME)
    if not ready():
        raise RuntimeError("safetensor_worker_not_ready")
    params = vram_guard.image_params()
    path = native_image.generate_image(
        model_path=MODELS.stable,
        prompt=prompt,
        negative_prompt="low quality, blurry, distorted, malformed, watermark, text artifacts",
        width=int(params.get("width", SETTINGS.image_width)),
        height=int(params.get("height", SETTINGS.image_height)),
        steps=int(params.get("steps", SETTINGS.image_steps)),
        guidance_scale=float(params.get("guidance_scale", SETTINGS.image_guidance)),
    )
    rel = path.relative_to(OUTPUT)
    return WorkerResult(worker=NAME, content=f"Generated image.\n\n![Generated image](/outputs/{rel})\n\nFile: `data/output/{rel}`")
