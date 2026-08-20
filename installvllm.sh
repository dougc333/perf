#!/bin/sh

apt update && apt upgrade -y
apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
libffi-dev liblzma-dev

curl https://pyenv.run | bash


export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"
eval "$(pyenv init -)"

pyenv install 3.12
pyenv global 3.12



curl -LsSf https://astral.sh/uv/install.sh | sh

export PATH="$HOME/.local/bin:$PATH"

uv venv --python 3.12 vllm-env
source vllm-env/bin/activate

uv self update
uv pip install -U vllm --torch-backend=cu129

hf auth login
hf download Qwen/Qwen3-0.6B --local-dir /workspace/models/Qwen3-0.6B

find /workspace/vllm-env/lib/python3.12/site-packages/nvidia \
  -name 'libcudart.so.13*' 2>/dev/null

export LD_LIBRARY_PATH=/workspace/vllm-env/lib/python3.12/site-packages/nvidia/cu13/lib:${LD_LIBRARY_PATH:-}

</site-packages/nvidia/cu13/lib:${LD_LIBRARY_PATH:-}                             (vllm-env) root@485008e876db:/workspace# python -c "
> import torch
> print('Torch:', torch.__version__)
> print('CUDA:', torch.version.cuda)
> import vllm
> print('vLLM:', vllm.__version__)
> "
Torch: 2.13.0+cu129
CUDA: 12.9

not cuda 13!!!

uv pip uninstall vllm torch torchvision torchaudio
uv pip install vllm --torch-backend=cu130


export LD_LIBRARY_PATH=/workspace/vllm-env/lib/python3.12/site-packages/nvidia/cu13/lib:${LD_LIBRARY_PATH:-}

VLLM_USE_FLASHINFER_SAMPLER=0 \
> HF_HUB_OFFLINE=1 \
> vllm serve /workspace/models/Qwen3-0.6B \
>   --served-model-name Qwen/Qwen3-0.6B \
>   --model-impl transformers \
>   --enforce-eager \
>   --max-model-len 2048 \
>   2>&1 | tee /workspace/vllm.log


VLLM_USE_FLASHINFER_SAMPLER=0 \
HF_HUB_OFFLINE=1 \
vllm serve /workspace/models/Qwen3-0.6B \
  --served-model-name Qwen/Qwen3-0.6B \
  --model-impl transformers \
  --enforce-eager \
  --max-model-len 2048 \
  2>&1 | tee /workspace/vllm.log

  VLLM_USE_FLASHINFER_SAMPLER=0 \
vllm serve Qwen/Qwen3-0.6B \
  --model-impl vllm \
  --enforce-eager


#export LD_LIBRARY_PATH=/workspace/vllm/lib/python3.12/site-packages/nvidia/cu13/lib:${LD_LIBRARY_PATH:-}
#echo 'export LD_LIBRARY_PATH=/workspace/vllm/lib/python3.12/site-packages/nvidia/cu13/lib:${LD_LIBRARY_PATH:-}' \
#  >> /workspace/vllm/bin/activate

#hf download Qwen/Qwen3-0.6B --local-dir /workspace/models/Qwen3-0.6B