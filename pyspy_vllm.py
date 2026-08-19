import os
import subprocess
import time
import urllib.request
import urllib.error

# 1. Set the environment variable BEFORE starting vLLM
os.environ["VLLM_USE_FLASHINFER_SAMPLER"] = "0"

print("1. Starting vllm serve subprocess...")
t0 = time.perf_counter()

# 2. Start vllm, letting it print directly to the console for easy debugging
server_process = subprocess.Popen(
    ["vllm", "serve", "Qwen/Qwen3-0.6B", "--model-impl", "transformers"],
)

child_pid = server_process.pid
print(f"\n   ✅ vllm server started with PID: {child_pid}")

print("2. Attaching py-spy to the vllm child process...")
log = open("pyspy.log", "w")
pyspy_process = subprocess.Popen(
    [
        "py-spy", "record", 
        "--pid", str(child_pid),          
        "--format", "speedscope", 
        "-o", "vllm_startup_profile.json",
        "--rate", "100", 
        "--duration", "600"
    ],
    stdout=log, 
    stderr=subprocess.STDOUT
)
print("   ✅ py-spy attached and recording.")

print("3. Waiting for vllm server to become healthy (polling /health)...")
ready = False
for i in range(120):  # Wait up to 120 seconds
    time.sleep(1)
    
    # Check if process died prematurely
    if server_process.poll() is not None:
        print(f"\n❌ vllm process crashed unexpectedly at {i} seconds!")
        break
        
    try:
        with urllib.request.urlopen("http://localhost:8000/health") as response:
            if response.status == 200:
                ready = True
                break
    except urllib.error.URLError:
        if i % 10 == 0:
            print(f"   ... still loading ({i}s)")
        continue

t1 = time.perf_counter()
if ready:
    print(f"\n🎉 SUCCESS! vllm serve is ready in {t1 - t0:.3f}s")
    print("py-spy is still recording. Press Ctrl+C to stop and save the profile.")
else:
    print(f"\n⚠️ vllm serve failed to start. Check the logs above for the exact error.")

try:
    server_process.wait()
except KeyboardInterrupt:
    print("\n\n🛑 Stopping server and py-spy...")
    server_process.terminate()
    pyspy_process.terminate()
    server_process.wait()
    pyspy_process.wait()
    print("✅ Cleanup complete.")
    print("👉 Open 'vllm_startup_profile.json' in https://www.speedscope.app/")