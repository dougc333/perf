"""Profile a HF model load with py-spy into a speedscope file.

Run directly (python runme_droplet.py) or via the installed perf-record script.
Writes hf_profile.speedscope.json (plus pyspy.log) in the current directory.
"""

import os
import signal
import subprocess
import time

OUTPUT = "hf_profile.speedscope.json"


def main() -> None:
    pid = os.getpid()
    print(f"Kernel PID: {pid}")

    with open("pyspy.log", "w") as log:
        profiler = subprocess.Popen(
            ["py-spy", "record", "--pid", str(pid), "--format", "speedscope", "-o", OUTPUT,
             "--rate", "100", "--duration", "600"],
            stdout=log, stderr=subprocess.STDOUT,
        )
        print("profiling started")
        time.sleep(2)  # let py-spy finish attaching before the interesting work runs
        print("py-spy attached, ready to profile")

        t0 = time.perf_counter()
        import transformers
        t1 = time.perf_counter()

        from transformers import AutoModelForCausalLM
        t2 = time.perf_counter()

        model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-0.6B")
        t3 = time.perf_counter()

        print(f"import transformers:  {t1 - t0:.3f}s")
        print(f"AutoModelForCausalLM: {t2 - t1:.3f}s")
        print(f"from_pretrained load: {t3 - t2:.3f}s")

        profiler.send_signal(signal.SIGINT)  # py-spy treats SIGINT as finish-recording-now
        profiler.wait(timeout=30)
    print(f"done — {OUTPUT} is ready")


if __name__ == "__main__":
    main()
