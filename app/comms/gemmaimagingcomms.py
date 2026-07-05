from __future__ import annotations

from app.workers import gemma, safetensor


def run(original_prompt: str, manager_task: str):
    prompt = manager_task or original_prompt
    if gemma.ready():
        try:
            refined = gemma.write(
                "Rewrite this as one clean Stable Diffusion prompt. Return only the image prompt text.\n\n"
                f"Original request:\n{original_prompt}\n\nWorker task:\n{manager_task}",
                max_tokens=220,
            )
            prompt = refined.content.strip() or prompt
        except Exception:
            prompt = manager_task or original_prompt
    result = safetensor.image(prompt)
    return gemma.final_check(original_prompt, result.content)
