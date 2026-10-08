#!/usr/bin/env python3
"""Waiter for the 1.6.7 timing A/B (job-a.py). Starts when: the device lock is free, no queue line ABOVE mine is still WAITING
(file position, rule 5), not actively swapping, load < 100, free memory >= 40 pct, pressure <= 2, disk >= 15 GB, no remoti-w6 xcodebuild.
Waits at most 8 h; job-a.py caps itself at 80 min; the lock is released in finally."""
import os, subprocess, time, shutil
G = "/Users/manu/Developer/shotfleet-rc-build/ab-1.6.7-maestro"; LOG = G + "/waiter.log"; LOCK = "/tmp/shotfleet-devices.lock"; QUEUE = "/tmp/shotfleet-device-queue.md"; MARK = "Same-build A/B on Maestro 2.0.10 vs 2.11.0 (maestro-version-compatibility session)"
def say(m): open(LOG, "a").write(time.strftime("%H:%M:%S ") + m + "\n")
def free_gb(): return shutil.disk_usage("/System/Volumes/Data").free / 2**30
def sysctl(k): return subprocess.run(["sysctl", "-n", k], capture_output=True, text=True).stdout.strip()
HIST = []  # (time, vm_stat Swapouts)
def swapouts():
    for l in subprocess.run(["vm_stat"], capture_output=True, text=True).stdout.splitlines():
        if l.startswith("Swapouts"): return int(l.split(":")[1].strip().rstrip("."))
    return 10**12
def free_mem_pct():
    for l in subprocess.run(["memory_pressure"], capture_output=True, text=True).stdout.splitlines():
        if "free percentage" in l: return int(l.split(":")[1].strip().rstrip("%"))
    return 0
def quiet():
    # coordinator 17:21: not actively swapping (Swapouts +< 2000 pages per 60 s window, 3 windows in a row) AND load < 100 AND free memory >= 40 % AND pressure <= 2
    now = time.time(); HIST.append((now, swapouts())); del HIST[:-200]
    def at(t):  # newest sample at or before t, else None
        c = [h for h in HIST if h[0] <= t]; return c[-1] if c else None
    pts = [at(now - 60 * k) for k in range(4)]
    if None in pts: return False
    if any(pts[k][1] - pts[k + 1][1] >= 2000 for k in range(3)): return False
    return (float(sysctl("vm.loadavg").strip("{} ").split()[0]) < 100 and free_mem_pct() >= 40
            and int(sysctl("kern.memorystatus_vm_pressure_level")) <= 2)

def turn():
    """True when no queue line above mine is still WAITING (a RUNNING line holds the lock, which is checked separately)."""
    lines = open(QUEUE).read().splitlines(); mine = [i for i, l in enumerate(lines) if MARK in l]
    return bool(mine) and not any(l.startswith("- ") and "WAITING" in l and "DONE" not in l for l in lines[:mine[0]])
def drop_queue_line():
    """Mark my line DONE with the shared helper (queue rule 6: atomic edit, never > or a rewrite)."""
    try:
        line = next(l for l in open(QUEUE).read().splitlines() if MARK in l)
        pre = line[:line.index(MARK) + len(MARK)]
        subprocess.run(["sh", "/Users/manu/Developer/shotfleet-rc-build/queue-edit.sh", "done", pre, pre + ": DONE %s, lock released, my simulators and emulators shut down" % time.strftime("%H:%M")], timeout=60)
    except (OSError, StopIteration, subprocess.TimeoutExpired): pass
def xcb_busy():
    return bool(subprocess.run("ps axo command | grep '[x]codebuild' | grep -E 'remoti-w6|D8640B97'", shell=True, capture_output=True, text=True).stdout.strip())
say("waiter armed (max 8 h)"); t0 = time.time()
while time.time() - t0 < 8 * 3600:
    try:
        if os.path.exists(LOCK) or not turn() or not quiet() or free_gb() < 15 or xcb_busy(): time.sleep(15); continue
        os.mkdir(LOCK)
    except FileExistsError: time.sleep(5); continue
    except Exception as e: say("check failed: %s" % e); time.sleep(15); continue
    open(LOCK + "/holder", "w").write("%s: Crossfit Tracker 1.6.7 timing A/B: iOS then Android phone, each on Maestro 2.0.10 and 2.11.0, shotfleet's own sims/emulators (iOS 26.4) | started %s | est. 45-60 min, hard limit 85 | waiter pid %d\n" % (MARK, time.strftime("%H:%M"), os.getpid()))
    say("lock taken")
    try:
        rc = subprocess.run(["python3", G + "/job-a.py"], timeout=85 * 60, stdout=open(G + "/job.out", "w"), stderr=subprocess.STDOUT).returncode; say("job rc %s" % rc)
    except subprocess.TimeoutExpired: say("job HARD LIMIT 60 min")
    finally:
        subprocess.run(["rm", "-rf", LOCK]); drop_queue_line(); say("lock released, queue line removed")
    raise SystemExit(0)
say("gave up after 8 h"); drop_queue_line()
