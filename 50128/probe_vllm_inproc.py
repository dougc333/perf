import os
os.environ["VLLM_ENABLE_V1_MULTIPROCESSING"] = "0"
import torch
from vllm import LLM
print("LLM import OK, building in-process engine...")
llm = LLM(model="/workspace/models/Qwen3-0.6B", model_impl="transformers", max_model_len=2048, enforce_eager=True, dtype="bfloat16")
print("ENGINE_READY", type(llm).__name__)
