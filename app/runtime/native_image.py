from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.runtime.config import OUTPUT, SETTINGS


@dataclass
class LoadedImageModel:
    path: Path
    pipe: Any


_LOCK = threading.Lock()
_CACHE: LoadedImageModel | None = None


def _deps_available() -> bool:
    try:
        import torch  # noqa: F401
        from diffusers import StableDiffusionPipeline  # noqa: F401
        from PIL import Image  # noqa: F401
        return True
    except Exception:
        return False


def ready(model_path: Path) -> bool:
    return model_path.exists() and _deps_available()


def load(model_path: Path) -> LoadedImageModel:
    if not model_path.exists():
        raise RuntimeError(f"safetensor_model_missing:{model_path}")

    global _CACHE
    with _LOCK:
        if _CACHE is not None and _CACHE.path == model_path:
            return _CACHE

        import torch
        from diffusers import StableDiffusionPipeline

        dtype = torch.float16 if SETTINGS.device == "cuda" and torch.cuda.is_available() else torch.float32
        if model_path.is_file():
            pipe = StableDiffusionPipeline.from_single_file(
                str(model_path),
                torch_dtype=dtype,
                local_files_only=True,
                safety_checker=None,
                requires_safety_checker=False,
            )
        else:
            pipe = StableDiffusionPipeline.from_pretrained(
                str(model_path),
                torch_dtype=dtype,
                local_files_only=True,
                safety_checker=None,
                requires_safety_checker=False,
            )

        if SETTINGS.device == "cuda" and torch.cuda.is_available():
            pipe = pipe.to("cuda")
            try:
                pipe.enable_attention_slicing()
            except Exception:
                pass
        else:
            pipe = pipe.to("cpu")

        _CACHE = LoadedImageModel(path=model_path, pipe=pipe)
        return _CACHE


def generate_image(
    *,
    model_path: Path,
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    steps: int,
    guidance_scale: float,
) -> Path:
    loaded = load(model_path)
    result = loaded.pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        num_inference_steps=steps,
        guidance_scale=guidance_scale,
    )
    image = result.images[0]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / f"symon_image_{len(list(OUTPUT.glob('symon_image_*.png'))) + 1:06d}.png"
    image.save(path)
    return path
