#!/bin/sh

curl -LsSf https://astral.sh/uv/install.sh | sh


uv venv --python 3.12 vllm-env
source vllm-env/bin/activate

uv self update
uv pip install -U vllm --torch-backend=cu129

VLLM_USE_FLASHINFER_SAMPLER=0 \
vllm serve Qwen/Qwen3-0.6B \
  --model-impl transformers \
  --enforce-eager

  VLLM_USE_FLASHINFER_SAMPLER=0 \
vllm serve Qwen/Qwen3-0.6B \
  --model-impl vllm \
  --enforce-eager
