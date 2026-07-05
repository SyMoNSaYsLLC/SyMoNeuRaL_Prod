from __future__ import annotations

from app.comms import gemmacodercomms, gemmaimagingcomms
from app.workers import gemma, qwen, safetensor


def answer(prompt: str, max_tokens: int = 768) -> tuple[str, str]:
    decision = gemma.decide(prompt)

    if decision.worker == "qwen":
        result = gemmacodercomms.run(prompt, decision.task, max_tokens)
    elif decision.worker == "safetensor":
        result = gemmaimagingcomms.run(prompt, decision.task)
    else:
        result = gemma.write(decision.task, max_tokens)

    return result.worker, result.content


def worker_readiness() -> dict[str, bool]:
    return {
        "gemma": gemma.ready(),
        "qwen": qwen.ready(),
        "safetensor": safetensor.ready(),
    }
