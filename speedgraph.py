import os, subprocess, signal, time
PID = os.getpid()
print(f"Kernel PID: {PID}")


log = open("pyspy.log", "w")
p = subprocess.Popen(
    ["py-spy", "record", "--pid", str(PID), "--format", "speedscope", "-o", "hf_profile.speedscope.json" ,
     "--rate", "100", "--duration", "600"],
    stdout=log, stderr=subprocess.STDOUT,
)
print("profiling started")

