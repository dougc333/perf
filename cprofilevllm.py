import os
import sys
import cProfile
import pstats
import time

# 1. Set environment variables to avoid known bugs
os.environ["VLLM_USE_FLASHINFER_SAMPLER"] = "0"

print("1. Starting internal vLLM profiling (no Docker permissions needed)...")
t0 = time.perf_counter()

# 2. Mock the command line arguments for vLLM
sys.argv = ["vllm", "serve", "Qwen/Qwen3-0.6B", "--model-impl", "transformers"]

# 3. Start the built-in Python profiler
profiler = cProfile.Profile()
profiler.enable()

try:
    # Import and run vLLM's main CLI function directly inside this script
    from vllm.entrypoints.cli.main import main as vllm_main
    print("2. Launching vLLM server internally... (this will block until you press Ctrl+C)")
    vllm_main()
except SystemExit:
    # vLLM might exit cleanly
    pass
except KeyboardInterrupt:
    print("\n\n🛑 Interrupted by user (Ctrl+C).")
finally:
    # 4. Stop profiling and save the results
    profiler.disable()
    t1 = time.perf_counter()
    print(f"\n✅ Profiling complete. Total recorded time: {t1 - t0:.3f}s")
    
    output_file = "vllm_startup_profile.txt"
    print(f"Saving profile to {output_file}...")
    
    with open(output_file, "w") as f:
        # Sort by 'cumulative' time (total time spent in a function and all functions it called)
        stats = pstats.Stats(profiler, stream=f)
        stats.sort_stats('cumulative')
        stats.print_stats(100) # Show the top 100 slowest functions
        
    print(f"👉 Open '{output_file}' to see the top 100 slowest functions during startup!")
    print("💡 Tip: Look for high numbers in the 'cumtime' column next to 'transformers' or 'vllm' functions.")