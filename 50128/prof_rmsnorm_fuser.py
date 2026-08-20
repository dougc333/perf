"""Profile the repeated FX tracing in recursive_replace / RMSNorm fuser path
(vLLM ticket #50128).

The bug: get_fuser() caches the pattern MATCH per module class, but
RMSNormFuser.fuse() calls fx_utils.trace(module) AGAIN for every instance
(to extract eps). Qwen3-0.6B has 51 RMSNorm instances, so recursive_replace
re-traces each one's forward even though the class was already matched.
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

# ---- instrumentation: count FX trace() calls -----------------------------
# fuser.py and fusers/rms_norm.py do 'from fx_utils import trace', so patch
# the names in THOSE modules, plus the canonical fx_utils.trace.
import collections
import inspect

trace_calls = collections.Counter()          # caller -> count
trace_by_module = collections.Counter()      # module class -> count

import vllm.model_executor.models.transformers.fx_utils as fx_utils
import vllm.model_executor.models.transformers.fuser as fuser_mod
import vllm.model_executor.models.transformers.fusers.rms_norm as rms_mod

_orig_trace = fx_utils.trace

def counting_trace(module):
    trace_by_module[type(module).__name__] += 1
    try:
        caller = inspect.currentframe().f_back
        caller_name = caller.f_globals.get("__name__", "?") + ":" + (caller.f_code.co_name or "?")
    except Exception:
        caller_name = "?"
    trace_calls[caller_name] += 1
    return _orig_trace(module)

fx_utils.trace = counting_trace
fuser_mod.trace = counting_trace
rms_mod.trace = counting_trace


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
        print("get_model total: %.3fs" % (t1 - t0), flush=True)
        print("MODEL_READY", type(model).__name__, flush=True)

    print("=== FX trace() call counts (by caller) ===", flush=True)
    for caller, n in trace_calls.most_common(10):
        print("  %4d  %s" % (n, caller), flush=True)
    print("=== trace() by module class (top 12) ===", flush=True)
    for cls, n in trace_by_module.most_common(12):
        print("  %4d  %s" % (n, cls), flush=True)
    print("  total trace() calls: %d" % sum(trace_by_module.values()), flush=True)

    if dist.is_initialized():
        dist.destroy_process_group()

if __name__ == "__main__":
    main()
