import time, measure_2

t0 = time.perf_counter()
import measure_2
t1 = time.perf_counter()

from transformers import AutoModelForCausalLM
t2 = time.perf_counter()

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B", dtype=measure_2.float16)
t3 = time.perf_counter()

print(f"import torch:            {t1 - t0:.3f}s")
print(f"import transformers:     {t2 - t1:.3f}s")
print(f"from_pretrained (load):  {t3 - t2:.3f}s")


