#!/usr/bin/env python3
"""Record the two device tapes (c3 iOS run, c4 Android run) under the shared device lock (docs/device-queue.md).

    python3 marketing/demo-video/record_devices.py [SESSION]     # detaches itself; follow PROGRESS (below)

The detached child waits (at most WAIT_H hours) until /tmp/shotfleet-devices.lock has been free for FREE_FOR_S seconds (so jobs
queued earlier go first), /tmp/shotfleet-quiet-check.sh passes and /tmp/shotfleet-rc-gate-done exists; then it takes the lock with
mkdir, runs each tape with a hard kill limit, shuts down only the simulators and emulators that appeared during its own run
(shotfleet pool names, 57xx emulator ports), and releases the lock. Run session.sh and tapes c1-c2 first (c2 writes the config).
"""
import os, re, subprocess, sys, time, signal, json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SESSION = Path(sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].startswith("--") else
               Path.home() / "Developer/shotfleet-rc-build/demo-video/session")
PROGRESS = SESSION.parent / "progress.log"
LOCK, QUIET, GATE = Path("/tmp/shotfleet-devices.lock"), "/tmp/shotfleet-quiet-check.sh", Path("/tmp/shotfleet-rc-gate-done")
TAPES = [("tapes/c3-run-ios.tape", 50 * 60), ("tapes/c4-run-android.tape", 45 * 60)]   # hard kill limit per step
WAIT_H, FREE_FOR_S, EST, HARD = 12, 180, 45, 95
POOLS = ("shotfleet-iphone-17-pro-max-", "shotfleet-ipad-pro-13-inch-m5")
ADB = Path.home() / "Library/Android/sdk/platform-tools/adb"

def log(msg):
    with open(PROGRESS, "a") as f: f.write(f"{time.strftime('%F %T')} devices: {msg}\n")

def sh(*cmd, timeout=60):
    try: return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except (OSError, subprocess.TimeoutExpired): return ""

def booted_pool_sims():
    devs = json.loads(sh("xcrun", "simctl", "list", "devices", "-j") or "{}").get("devices", {})
    return {d["udid"] for v in devs.values() for d in v if d.get("state") == "Booted" and d.get("name", "").startswith(POOLS)}

def emulators_57xx():
    return {l.split()[0] for l in sh(str(ADB), "devices").splitlines() if l.startswith("emulator-57")}

def our_shotfleet_pids():
    """shotfleet runs started from THIS checkout's shotfleet.py, plus their descendants (maestro, xcrun...)."""
    pids = {p for p in sh("pgrep", "-f", f"{REPO}/shotfleet.py run").split() if p}
    todo = list(pids)
    while todo:
        for c in sh("pgrep", "-P", todo.pop()).split():
            if c not in pids: pids.add(c); todo.append(c)
    return pids

GATE_LOG = Path.home() / "Developer/shotfleet-rc-build/0.1.3/g3-013c.log"
MIN_FREE_PCT = 40

def others_done():
    """Coordinator, 20:43: start only after the 0.1.3 gate rerun ('lock released' in its log) and the Tart VM agent
    (its queue line marked DONE, or its branch pushed and it no longer holds the lock)."""
    gate = GATE_LOG.is_file() and "lock released" in GATE_LOG.read_text(errors="replace")
    q = Path("/tmp/shotfleet-device-queue.md").read_text(errors="replace") if Path("/tmp/shotfleet-device-queue.md").exists() else ""
    vm_line_done = any(re.search(r"tart|\bVM\b", l, re.I) and "DONE" in l for l in q.splitlines())
    return gate and vm_line_done   # 22:36: the VM agent must mark its queue line DONE (its branch is pushed but it may still run)

def free_pct():
    m = re.search(r"free percentage: *(\d+)%", sh("memory_pressure"))
    return int(m.group(1)) if m else 0

def run_tape(tape, limit):
    t0 = time.time(); log(f"start {tape} (hard limit {limit // 60} min)")
    p = subprocess.Popen(["vhs", tape], cwd=SESSION, stdout=open(SESSION / "rec" / (Path(tape).stem + ".vhs.log"), "w"),
                         stderr=subprocess.STDOUT, start_new_session=True)
    try: rc = p.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        log(f"KILL {tape}: over {limit // 60} min")
        for pid in our_shotfleet_pids(): sh("kill", "-TERM", pid)
        time.sleep(20)
        for pid in our_shotfleet_pids(): sh("kill", "-KILL", pid)
        os.killpg(p.pid, signal.SIGKILL); p.wait(); rc = -9
    log(f"end {tape} rc={rc} after {time.time() - t0:.0f} s; mp4 {'written' if (SESSION / 'rec' / (Path(tape).stem + '.mp4')).is_file() else 'MISSING'}")
    return rc

def child():
    deadline, free_since, last_note = time.time() + WAIT_H * 3600, None, 0
    log(f"waiter started (pid {os.getpid()}), waiting for the lock")
    while True:
        if time.time() > deadline: log("gave up waiting"); return
        if LOCK.exists(): free_since = None
        else:
            free_since = free_since or time.time()
            q = subprocess.run(["sh", QUIET], capture_output=True, text=True)
            if time.time() - free_since >= FREE_FOR_S and q.returncode == 0 and free_pct() >= MIN_FREE_PCT and others_done():
                try: LOCK.mkdir()
                except FileExistsError: free_since = None; continue
                break
            if time.time() - last_note > 600: log(f"lock free, waiting: {q.stdout.strip()}; free {free_pct()}%; gate+VM done: {others_done()}"); last_note = time.time()
        time.sleep(30)
    (LOCK / "holder").write_text(f"Demo video recording (coordinator) | fixture run iOS+Android | started {time.strftime('%H:%M')} | "
                                 f"est. {EST} min, hard limit {HARD}\n")
    log(f"LOCK TAKEN; {subprocess.run(['sh', QUIET], capture_output=True, text=True).stdout.strip()}; "
        f"disk {sh('df', '-h', str(SESSION)).splitlines()[-1].split()[3]} free")
    sims0, emus0 = booted_pool_sims(), emulators_57xx()
    try:
        for tape, limit in TAPES: run_tape(tape, limit)
    finally:
        for u in booted_pool_sims() - sims0: sh("xcrun", "simctl", "shutdown", u); log(f"shut down my simulator {u}")
        for e in emulators_57xx() - emus0: sh(str(ADB), "-s", e, "emu", "kill"); log(f"killed my emulator {e}")
        if (LOCK / "holder").read_text().startswith("Demo video recording"):
            subprocess.run(["rm", "-rf", str(LOCK)]); log("LOCK RELEASED")
        with open("/tmp/shotfleet-device-queue.md", "a") as f:
            f.write(f"- {time.strftime('%Y-%m-%d %H:%M')} Demo video recording: DONE, my simulators/emulators are shut down, lock RELEASED; my queue line is void.\n")

if __name__ == "__main__":
    if "--child" in sys.argv: child()
    else:
        p = subprocess.Popen([sys.executable, __file__, "--child", str(SESSION)], start_new_session=True,
                             stdout=open(SESSION / "rec" / "record_devices.out", "a"), stderr=subprocess.STDOUT)
        print(f"detached waiter pid {p.pid}; progress: {PROGRESS}")
