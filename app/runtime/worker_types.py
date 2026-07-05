from dataclasses import dataclass
from typing import Literal

WorkerName = Literal["gemma", "qwen", "safetensor"]

@dataclass(frozen=True)
class WorkerDecision:
    worker: WorkerName
    task: str
    check: str = ""

@dataclass(frozen=True)
class WorkerResult:
    worker: str
    content: str
    ok: bool = True
    error: str | None = None
