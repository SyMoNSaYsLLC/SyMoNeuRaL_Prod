from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import symoneural
from app.workers import vram_guard

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="SyMoNeuRaL MoE")

WEB_ROOT = ROOT / "apps" / "web"
STATIC_ROOT = WEB_ROOT / "static"
if STATIC_ROOT.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_ROOT)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT)), name="outputs")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = "symoneural_moe"
    messages: list[ChatMessage]
    max_tokens: int | None = 768
    stream: bool | None = False


def latest_user(messages: list[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content.strip()
    return ""


@app.get("/")
async def root():
    index = WEB_ROOT / "index.html"
    if not index.exists():
        raise HTTPException(500, "web_index_missing")
    return FileResponse(index)


@app.get("/health")
async def health():
    workers = symoneural.worker_readiness()
    return {
        "ok": all(workers.values()),
        "service": "symoneural_moe",
        "vram": vram_guard.status(),
        "workers": workers,
    }


@app.get("/v1/models")
async def models():
    return {"object": "list", "data": [{"id": "symoneural_moe", "object": "model"}]}


@app.post("/v1/chat/completions")
async def chat(req: ChatRequest):
    prompt = latest_user(req.messages)
    if not prompt:
        raise HTTPException(400, "missing user prompt")
    if req.stream:
        raise HTTPException(400, "streaming is not enabled for this production bridge")

    try:
        model, content = symoneural.answer(prompt, req.max_tokens or 768)
    except (NotImplementedError, RuntimeError) as exc:
        raise HTTPException(503, str(exc)) from exc

    return {
        "id": "symon-chatcmpl-local",
        "object": "chat.completion",
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "requested_max_tokens": req.max_tokens,
        },
    }


@app.post("/completion")
async def completion(payload: dict[str, Any]):
    prompt = str(payload.get("prompt") or payload.get("content") or "").strip()
    if not prompt:
        raise HTTPException(400, "missing prompt")
    try:
        model, content = symoneural.answer(prompt, 768)
    except (NotImplementedError, RuntimeError) as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"content": content, "model": model, "stop": True}


@app.get("/props")
async def props():
    return {"model_path": "symoneural_moe", "modalities": ["text", "image"], "total_slots": 1}


@app.get("/slots")
async def slots():
    return [{"id": 0, "state": 0}]


@app.get("/tools")
async def tools():
    return {"tools": [], "tool_choice": "none"}


@app.post("/v1/streams/lookup")
async def streams_lookup(payload: dict[str, Any]):
    return {"id": payload.get("id"), "found": False, "stream": None}


@app.get("/metrics")
async def metrics():
    current = vram_guard.status()
    lines = ["symoneural_manager_up 1"]
    if current.get("used_gb") is not None:
        lines.append(f"symoneural_vram_used_gb {current['used_gb']}")
    if current.get("total_gb") is not None:
        lines.append(f"symoneural_vram_total_gb {current['total_gb']}")
    return PlainTextResponse("\n".join(lines) + "\n")
