from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.runtime.config import SETTINGS


@dataclass
class LoadedTextModel:
    name: str
    path: Path
    tokenizer: Any
    model: Any
    torch: Any


_LOCK = threading.Lock()
_CACHE: dict[str, LoadedTextModel] = {}


def _deps_available() -> bool:
    try:
        import torch  # noqa: F401
        from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: F401
        return True
    except Exception:
        return False


def ready(model_path: Path) -> bool:
    return model_path.exists() and _deps_available()


def _dtype(torch: Any):
    if SETTINGS.device == "cuda" and torch.cuda.is_available():
        if torch.cuda.is_bf16_supported():
            return torch.bfloat16
        return torch.float16
    return torch.float32


def load(name: str, model_path: Path) -> LoadedTextModel:
    if not model_path.exists():
        raise RuntimeError(f"{name}_model_missing:{model_path}")

    with _LOCK:
        if name in _CACHE:
            return _CACHE[name]

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True, trust_remote_code=True)
        if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
            tokenizer.pad_token = tokenizer.eos_token

        kwargs: dict[str, Any] = {
            "local_files_only": True,
            "trust_remote_code": True,
            "torch_dtype": _dtype(torch),
        }
        if SETTINGS.device == "cuda" and torch.cuda.is_available():
            kwargs["device_map"] = "auto"
        else:
            kwargs["device_map"] = None

        model = AutoModelForCausalLM.from_pretrained(str(model_path), **kwargs)
        if SETTINGS.device != "cuda" or not torch.cuda.is_available():
            model = model.to("cpu")

        loaded = LoadedTextModel(name=name, path=model_path, tokenizer=tokenizer, model=model, torch=torch)
        _CACHE[name] = loaded
        return loaded


def unload(name: str | None = None) -> None:
    with _LOCK:
        if name is None:
            _CACHE.clear()
        else:
            _CACHE.pop(name, None)


def generate(
    *,
    name: str,
    model_path: Path,
    system: str,
    prompt: str,
    max_new_tokens: int,
    temperature: float,
) -> str:
    loaded = load(name, model_path)
    tokenizer = loaded.tokenizer
    model = loaded.model
    torch = loaded.torch

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    if hasattr(tokenizer, "apply_chat_template"):
        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        )
        attention_mask = torch.ones_like(input_ids)
    else:
        text = f"System:\n{system}\n\nUser:\n{prompt}\n\nAssistant:\n"
        encoded = tokenizer(text, return_tensors="pt")
        input_ids = encoded["input_ids"]
        attention_mask = encoded.get("attention_mask")

    device = getattr(model, "device", None)
    if device is not None:
        input_ids = input_ids.to(device)
        if attention_mask is not None:
            attention_mask = attention_mask.to(device)

    do_sample = temperature > 0
    with torch.inference_mode():
        output = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            do_sample=do_sample,
            temperature=temperature if do_sample else None,
            top_p=0.95 if do_sample else None,
            repetition_penalty=1.05,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    new_tokens = output[0][input_ids.shape[-1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def compact_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise
