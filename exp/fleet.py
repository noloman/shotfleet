#!/usr/bin/env python3
"""Fleet test: boot N read-only emulators of one AVD, apply identical load, sample host memory/CPU.

usage: fleet.py <avd> <n> <label> [--settle 120] [--load 300]
Writes exp/results/<label>.json (samples + per-launch latencies + summary).
"""
import json, os, re, statistics, subprocess, sys, threading, time

SDK = os.path.expanduser("~/Library/Android/sdk")
EMU = f"{SDK}/emulator/emulator"
PAGE = 16384
# app under test (exp/app-under-test.apk, preinstalled on every base AVD)
APP = "me.manulorenzo.crossfittracker.android.debug/me.manulorenzo.crossfittracker.android.presentation.MainActivity"
BASE_PORT = 5600

def sh(cmd, timeout=60):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return ""

def adb(serial, cmd, timeout=60):
    return sh(f"adb -s {serial} {cmd}", timeout)

def host_stats():
    vm = sh("vm_stat")
    get = lambda k: int(re.search(rf"{k}:\s+(\d+)", vm).group(1))
    swap = re.search(r"used = ([\d.]+)M", sh("sysctl vm.swapusage")).group(1)
    return {
        "free_mb": get("Pages free") * PAGE // 2**20,
        "compressor_mb": get("Pages occupied by compressor") * PAGE // 2**20,
        "swapins": get("Swapins"), "swapouts": get("Swapouts"),
        "swap_used_mb": float(swap),
        "pressure": int(sh("sysctl -n kern.memorystatus_vm_pressure_level").strip() or 0),
        "load1": float(sh("sysctl -n vm.loadavg").split()[1]),
    }

def fleet_pids(avd):
    out = sh(f"pgrep -f 'qemu-system.*-avd {avd} '")
    return [int(p) for p in out.split()]

def proc_stats(pids):
    rss = cpu = fp = 0.0
    for p in pids:
        line = sh(f"ps -o rss=,%cpu= -p {p}").split()
        if len(line) == 2:
            rss += int(line[0]) / 1024; cpu += float(line[1])
        m = re.search(r"phys_footprint: (\d+) MB", sh(f"footprint -p {p}", 30))
        if m: fp += int(m.group(1))
    return {"rss_mb": round(rss), "cpu_pct": round(cpu, 1), "footprint_mb": round(fp)}

def kill_fleet(avd, serials):
    for s in serials: adb(s, "emu kill", 15)
    time.sleep(10)
    sh(f"pkill -9 -f 'qemu-system.*-avd {avd} '")
    time.sleep(3)

def main():
    avd, n, label = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    args = dict(zip(sys.argv[4::2], sys.argv[5::2]))
    settle, load = int(args.get("--settle", 120)), int(args.get("--load", 300))
    serials = [f"emulator-{BASE_PORT + 2*i}" for i in range(n)]
    assert not fleet_pids(avd), f"{avd} already running"

    base = host_stats()
    t0 = time.time()
    launch = lambda i: subprocess.Popen(
        f"{EMU} -avd {avd} -port {BASE_PORT + 2*i} -read-only -no-window -no-audio "
        f"-no-boot-anim -no-snapshot >> /tmp/fleet_{i}.log 2>&1", shell=True)
    procs = []
    for i in range(n):
        procs.append(launch(i))
        time.sleep(2)  # stagger so adb port allocation doesn't race

    # emulator 37.1.5 sometimes aborts at startup ("set thread local GL render thread info twice");
    # relaunch dead instances, up to 2 times each
    boot, relaunches = {}, [0] * n
    while len(boot) < n and time.time() - t0 < 900:
        for i, s in enumerate(serials):
            if s in boot: continue
            if procs[i].poll() is not None and relaunches[i] < 2:
                relaunches[i] += 1; procs[i] = launch(i)
            elif adb(s, "shell getprop sys.boot_completed", 10).strip() == "1":
                boot[s] = round(time.time() - t0, 1)
        time.sleep(3)
    if len(boot) < n:
        kill_fleet(avd, serials)
        sys.exit(f"only {len(boot)}/{n} booted within 900s")

    # sanity: record how many packages are disabled on each instance (proves which base booted)
    disabled = {s: len(adb(s, "shell pm list packages -d").split()) for s in serials}
    missing = [s for s in serials if not adb(s, f"shell pm path {APP.split('/')[0]}").strip()]
    if missing:
        kill_fleet(avd, serials); sys.exit(f"app under test missing on {missing}")
    time.sleep(settle)

    samples, launches, stop = [], {s: [] for s in serials}, threading.Event()

    def worker(s):
        while not stop.is_set():
            # -S force-stops first so every launch is a cold start
            out = adb(s, f"shell am start -S -W -n {APP}", 60)
            m = re.search(r"WaitTime: (\d+)", out)
            launches[s].append(int(m.group(1)) if m else None)  # None = failed/timeout
            time.sleep(3)

    threads = [threading.Thread(target=worker, args=(s,), daemon=True) for s in serials]
    for t in threads: t.start()
    pids = fleet_pids(avd)
    end = time.time() + load
    while time.time() < end:
        samples.append({"t": round(time.time() - t0), **host_stats(), **proc_stats(pids)})
        time.sleep(10)
    stop.set()
    for t in threads: t.join(90)

    anr = sum(adb(s, "shell dumpsys activity processes").count("notResponding=true") for s in serials)
    am_kills = sum(int(adb(s, "shell 'logcat -d -b events | grep -c am_kill'").strip() or 0) for s in serials)
    kill_fleet(avd, serials)

    lat = [x for v in launches.values() for x in v if x is not None]
    fails = sum(x is None for v in launches.values() for x in v)
    q = lambda xs, p: sorted(xs)[min(len(xs) - 1, int(p * len(xs)))] if xs else None
    last = samples[-3:]
    summary = {
        "label": label, "avd": avd, "n": n,
        "boot_s_max": max(boot.values()), "boot_s_median": statistics.median(boot.values()),
        "disabled_pkgs": sorted(set(disabled.values())), "relaunches": sum(relaunches),
        "launches": len(lat), "launch_fail": fails,
        "launch_ms_p50": q(lat, .5), "launch_ms_p90": q(lat, .9),
        "fleet_rss_mb": round(statistics.mean(s["rss_mb"] for s in last)),
        "fleet_footprint_mb": round(statistics.mean(s["footprint_mb"] for s in last)),
        "fleet_cpu_pct": round(statistics.mean(s["cpu_pct"] for s in samples), 1),
        "swapouts_during": samples[-1]["swapouts"] - base["swapouts"],
        "swapins_during": samples[-1]["swapins"] - base["swapins"],
        "swap_growth_mb": round(samples[-1]["swap_used_mb"] - base["swap_used_mb"]),
        "compressor_growth_mb": samples[-1]["compressor_mb"] - base["compressor_mb"],
        "pressure_max": max(s["pressure"] for s in samples),
        "anr": anr, "am_kills": am_kills,
        "host_before": {k: base[k] for k in ("load1", "pressure", "swap_used_mb", "free_mb")},
    }
    os.makedirs("exp/results", exist_ok=True)
    json.dump({"summary": summary, "baseline": base, "boot": boot, "samples": samples, "launches": launches},
              open(f"exp/results/{label}.json", "w"), indent=1)
    print(json.dumps(summary))

if __name__ == "__main__":
    main()
