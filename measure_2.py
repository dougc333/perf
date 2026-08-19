"""Measure how long importing torch / transformers and loading a HF model takes.

Run directly (python measure_2.py) or via the installed perf-measure script.
"""

import time


def main() -> None:
    t0 = time.perf_counter()
    import torch
    t1 = time.perf_counter()

    from transformers import AutoModelForCausalLM
    t2 = time.perf_counter()

    model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B", dtype=torch.float16)
    t3 = time.perf_counter()

    print(f"import torch:            {t1 - t0:.3f}s")
    print(f"import transformers:     {t2 - t1:.3f}s")
    print(f"from_pretrained (load):  {t3 - t2:.3f}s")
    print(f"model loaded: {type(model).__name__}")


if __name__ == "__main__":
    main()
