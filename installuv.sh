#!/bin/sh

curl -LsSf https://astral.sh/uv/install.sh | sh

/root/.local/bin/uv venv venv
source venv/bin/activate


uv pip install vllm --torch-backend=auto