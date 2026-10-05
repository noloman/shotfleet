#!/usr/bin/env python3
"""run_modes.py <vtest binary> <image> [mode ...]: each mode in its own process under a hard 30 s limit.
Prints one line per mode: answered/timed out, wall seconds. Kills only the child it started (own process group)."""
import json, os, signal, subprocess, sys, time

exe, image, *modes = sys.argv[1:]
for mode in modes or ["default", "cpu", "fast", "fastcpu"]:
    t0 = time.time()
    p = subprocess.Popen([exe, mode, image], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = p.communicate(timeout=30)
        print(f"{mode:8} answered in {time.time() - t0:5.1f}s exit={p.returncode} {out.strip()[:200]} {err.strip()[:150]}", flush=True)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL); p.communicate()
        print(f"{mode:8} NO ANSWER in 30s (killed its own process)", flush=True)
