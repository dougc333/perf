import os, subprocess, time
import vllm

PID = os.getpid()
print(f"PID: {PID}")

log = open("pyspy.log", "w")
p = subprocess.Popen(
    ["py-spy", "record", "--pid", str(PID), "--format", "speedscope", "-o", "hf_profile.speedscope.json",
     "--rate", "100", "--duration", "600"],
    stdout=log, stderr=subprocess.STDOUT,
)
time.sleep(2)
print("py-spy attached")
import time

t0 = time.perf_counter()
import vllm
t1 = time.perf_counter()
print(f"import vllm: {t1 - t0:.3f}s")

vllm serve Qwen/Qwen3-0.6B --model-impl transformers
t2 = time.perf_counter()


print(f"import transformers:  {t1 - t0:.3f}s")
print(f"vllm: {t2 - t1:.3f}s")
