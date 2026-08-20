"""Profile the RMSNorm fuser path in vLLM's Transformers backend (ticket #50128).

Reproduces the repeated FX tracing: recursive_replace -> RMSNormFuser.fuse
calls trace(module) once per instance even though get_fuser already matched
the class. Qwen3-0.6B has ~51 RMSNorm instances (24 layers x 2 + final + q/k).
"""

import os
import time

os.environ.setdefault("VLLM_ENABLE_V1_MULTIPROCESSING", "0")

import torch.distributed as dist

from vllm.config import VllmConfig, set_current_vllm_config
from vllm.distributed.parallel_state import (
    init_distributed_environment,
    initialize_model_parallel,
)
from vllm.engine.arg_utils import EngineArgs
from vllm.model_executor.model_loader import get_model


def main():
    args = EngineArgs(
        model="/workspace/models/Qwen3-0.6B",
        model_impl="transformers",
        max_model_len=2048,
        enforce_eager=True,
        dtype="bfloat16",
    )
    vllm_config: VllmConfig = args.create_engine_config()
    print("VllmConfig built", flush=True)

    with set_current_vllm_config(vllm_config):
        init_distributed_environment(
            world_size=1, rank=0, local_rank=0,
            distributed_init_method="env://", backend="nccl",
        )
        initialize_model_parallel(tensor_model_parallel_size=1,
                                  pipeline_model_parallel_size=1)
        print("dist initialized", flush=True)

        t0 = time.perf_counter()
        model = get_model(vllm_config=vllm_config)
        t1 = time.perf_counter()
        print(f"get_model (recursive_replace incl.): {t1 - t0:.3f}s", flush=True)
        print("MODEL_READY", type(model).__name__, flush=True)

    if dist.is_initialized():
        dist.destroy_process_group()

if __name__ == "__main__":
    main()
