"""Tiny test script for the droplet runner API."""
import json
import time

print("hello from example.py", flush=True)
for i in range(3):
    print(f"step {i}", flush=True)
    time.sleep(0.3)
with open("example.out.json", "w") as fh:
    json.dump({"example": True, "steps": 3}, fh)
print("done", flush=True)
