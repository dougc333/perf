
#!/usr/bin/env bash


# 1. Downgrade transformers to the compatible version
pip install transformers==4.51.1

# 2. Ensure vLLM is fully up-to-date (Qwen3 support is very recent)
pip install --upgrade vllm

# 3. Clear any potentially corrupted/cached model config
rm -rf ~/.cache/huggingface/hub/models--Qwen--Qwen3-0.6B