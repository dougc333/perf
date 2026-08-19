import subprocess
import time
import urllib.request
import urllib.error

print("1. Starting vllm serve subprocess...")
t0 = time.perf_counter()

# Start vllm as a subprocess
server_process = subprocess.Popen(
    ["vllm", "serve", "Qwen/Qwen3-0.6B", "--model-impl", "transformers"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# Get the CHILD process PID (this is what we want to profile!)
child_pid = server_process.pid
print(f"   vllm server started with PID: {child_pid}")

print("2. Attaching py-spy to the vllm child process...")
log = open("pyspy.log", "w")
pyspy_process = subprocess.Popen(
    [
        "py-spy", "record", 
        "--pid", str(child_pid),          # <-- TARGET THE CHILD PID HERE
        "--format", "speedscope", 
        "-o", "vllm_startup_profile.json",
        "--rate", "100", 
        "--duration", "600"
    ],
    stdout=log, 
    stderr=subprocess.STDOUT
)

print("3. Waiting for vllm server to become healthy...")
ready = False
for _ in range(120):  # Wait up to 120 seconds
    time.sleep(1)
    try:
        with urllib.request.urlopen("http://localhost:8000/health") as response:
            if response.status == 200:
                ready = True
                break
    except urllib.error.URLError:
        continue

t1 = time.perf_counter()
if ready:
    print(f"✅ vllm serve is ready: {t1 - t0:.3f}s")
else:
    print(f"⚠️ vllm serve did not become healthy in time. Check pyspy.log for errors.")

print("\nServer is running. py-spy is recording. Press Ctrl+C to stop both.")
try:
    server_process.wait()
except KeyboardInterrupt:
    print("\nStopping server and py-spy...")
    server_process.terminate()
    pyspy_process.terminate()
    server_process.wait()
    pyspy_process.wait()
    print("Cleanup complete. Open 'vllm_startup_profile.json' in https://www.speedscope.app/")