# SyMoNeuRaL CLEAN

SyMoNeuRaL CLEAN is the single-public-entry backend for the `symoneural_moe` service.

## Production status

Production-ready native Python worker wiring is implemented in this reviewed build.

The public process is only the FastAPI manager served by uvicorn on port `8000`. Gemma, Qwen, and safetensor image generation are repo-owned Python workers called by name from backend modules. The application does not use llama.cpp worker calls, old worker ports, worker URLs, or external local server assumptions.

## Architecture

```text
user request
  -> app/main.py                     public FastAPI bridge
  -> app/symoneural.py               name-based orchestrator
  -> app/workers/gemma.py            Gemma manager/writer
       -> app/comms/gemmacodercomms.py -> app/workers/qwen.py
       -> app/comms/gemmaimagingcomms.py -> app/workers/safetensor.py
  -> optional Gemma final check
  -> response returned through the public manager
```

Only one public service is expected:

```text
8000  symoneural_moe FastAPI / web UI
```

## Worker files

```text
app/main.py                       public FastAPI bridge
app/symoneural.py                 name-based orchestrator
app/workers/gemma.py              Gemma manager/writer native Python worker
app/workers/qwen.py               Qwen coder native Python worker
app/workers/safetensor.py         Stable safetensor native Python image worker
app/workers/vram_guard.py         VRAM policy and safety checks
app/comms/gemmacodercomms.py      Gemma -> Qwen handoff/check
app/comms/gemmaimagingcomms.py    Gemma -> safetensor handoff/check
app/runtime/config.py             model path and runtime settings
app/runtime/native_text.py        repo-owned text inference adapter
app/runtime/native_image.py       repo-owned image inference adapter
app/runtime/worker_types.py       shared typed results/decisions
```

## Model paths

The workers load local model assets only. Set these environment variables when your local paths differ from the defaults:

```bash
export SYMON_GEMMA_MODEL="$HOME/SyMoNeuRaL_CLEAN/models/llm/gemma"
export SYMON_QWEN_MODEL="$HOME/SyMoNeuRaL_CLEAN/models/llm/qwen"
export SYMON_STABLE_MODEL="$HOME/SyMoNeuRaL_CLEAN/models/sd/v1-5-pruned-emaonly.safetensors"
```

Expected defaults:

```text
models/llm/gemma
models/llm/qwen
models/sd/v1-5-pruned-emaonly.safetensors
```

Gemma and Qwen should be Hugging Face `transformers`-loadable local directories. The image worker accepts either a diffusers directory or a Stable Diffusion `.safetensors` checkpoint supported by `diffusers` `from_single_file`.

## VRAM policy

`app/workers/vram_guard.py` enforces the configured GPU limits before heavy work:

```text
Target: 14.0 GB
Hard limit: 15.2 GB
```

Text token limits and image dimensions/steps are reduced when VRAM approaches the target.

## Install dependencies

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

## Start

```bash
./scripts/start.sh
```

## Stop

```bash
./scripts/stop.sh
```

## Status

```bash
./scripts/status.sh
```

## Tests and audit

```bash
./scripts/test.sh
python3 production_audit.py
```

## Production router requirement

If publishing from your router, forward only the public manager service:

```text
WAN 8000 -> Debian host 8000
```

Do not expose worker model internals separately. All Gemma, Qwen, and safetensor handoffs happen by Python function calls inside the backend.
