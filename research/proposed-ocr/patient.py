#!/usr/bin/env python3
"""patient.py <exe> <mode> <image> <limit_s>: one run with a long limit; prints seconds and the helper's answer.
Also prints ANECompilerService CPU every 10 s (read only: ps)."""
import os, signal, subprocess, sys, time

exe, mode, image, limit = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
t0 = time.time()
p = subprocess.Popen([exe, mode, image], stdout=subprocess.PIPE, text=True, start_new_session=True,
                     env={**os.environ, "VT_CHARS": os.environ.get("VT_CHARS", "600")})
last = 0
while p.poll() is None and time.time() - t0 < limit:
    time.sleep(1)
    if time.time() - last >= 10:
        last = time.time()
        cpu = subprocess.run("ps -axo pcpu,comm | grep ANECompilerService | grep -v grep", shell=True, capture_output=True, text=True).stdout.split()[:1]
        print(f"  {time.time() - t0:5.0f}s ANECompilerService cpu {cpu}", flush=True)
if p.poll() is None:
    os.killpg(p.pid, signal.SIGKILL); p.wait(); print(f"NO ANSWER in {limit:.0f}s")
else:
    print(f"answered in {time.time() - t0:.1f}s: {p.stdout.read()[:1500]}")
