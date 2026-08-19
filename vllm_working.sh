#!/usr/bin/env bash



export VLLM_USE_FLASHINFER_SAMPLER=0
vllm serve Qwen/Qwen3-0.6B --model-impl transformers