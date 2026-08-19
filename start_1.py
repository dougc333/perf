import os, subprocess, signal, time
PID = os.getpid()
print(f"Kernel PID: {PID}")

log = open("pyspy.log", "w")
p = subprocess.Popen(
    ["py-spy", "record", "--pid", str(PID), "--format", "speedscope", "-o", "hf_profile.speedscope.json",
     "--rate", "100", "--duration", "600"],
    stdout=log, stderr=subprocess.STDOUT,
)
print("profiling started")
time.sleep(2)  # let py-spy actually finish attaching before anything worth capturing runs
print("py-spy attached, ready to profile")

import time

t0 = time.perf_counter()
import transformers
t1 = time.perf_counter()
print(f"import transformers: {t1 - t0:.3f}s")

from transformers import AutoModelForCausalLM
t2 = time.perf_counter()

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B")
t3 = time.perf_counter()

print(f"import transformers:  {t1 - t0:.3f}s")
print(f"AutoModelForCausalLM: {t2 - t1:.3f}s")
print(f"from_pretrained load: {t3 - t2:.3f}s")

p.send_signal(signal.SIGINT)   # py-spy treats this as "finish recording now"
p.wait(timeout=30)
log.close()
print("done — hf_profile.speedscope.json is ready")