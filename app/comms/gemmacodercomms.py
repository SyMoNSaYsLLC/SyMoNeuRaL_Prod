from __future__ import annotations

from app.workers import gemma, qwen


def run(original_prompt: str, manager_task: str, max_tokens: int):
    task = (
        "Gemma manager assigned this coding task to Qwen.\n\n"
        f"Original request:\n{original_prompt}\n\n"
        f"Worker task:\n{manager_task}\n\n"
        "Return the final code, patch, or command answer only."
    )
    draft = qwen.code(task, max_tokens=max_tokens)
    return gemma.final_check(original_prompt, draft.content)
