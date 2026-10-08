#!/usr/bin/env python3
"""Same-build A/B of Maestro 2.0.10 vs 2.11.0: Crossfit Tracker 1.6.7 (build 58), the showcase flows, shotfleet from origin/main (SRC.txt), all languages the app ships,
iPhone 17 Pro Max on iOS 26.4 and the shotfleet_android phone AVD, parallel left to shotfleet's own default (it logs what it chose). Order: iOS 2.0.10, iOS 2.11.0, Android 2.11.0, Android 2.0.10
(the order flips per platform so neither version is always first). Assumes the device lock is held. Each run is killed after 30 min; the whole job after 80 min."""
import os, subprocess, time, signal, json, glob, shutil, re
A = "/Users/manu/Developer/shotfleet-rc-build/ab-1.6.7-maestro"; OUT = A + "/out-" + time.strftime("%Y%m%d-%H%M%S"); os.makedirs(OUT)
BIN = {"2.0.10": os.path.expanduser("~/.maestro/bin"), "2.11.0": os.path.expanduser("~/.maestro-tests/2.11.0/bin")}
T0 = time.time(); LOG = open(OUT + "/job.log", "a"); RES = []
def say(m): LOG.write(time.strftime("%H:%M:%S ") + m + "\n"); LOG.flush()
def sh(c, t=60): return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t).stdout
def load(): return sh("sysctl -n vm.loadavg").strip()
def swap(): return sh("sysctl -n vm.swapusage").strip()
def pressure(): return sh("sysctl -n kern.memorystatus_vm_pressure_level").strip()
def one(platform, ver):
    name = "%s-%s" % (platform, ver); d = OUT + "/" + name; os.makedirs(d)
    env = dict(os.environ, PATH=BIN[ver] + ":" + os.environ["PATH"], MAESTRO_CLI_NO_ANALYTICS="1", MAESTRO_DISABLE_UPDATE_CHECK="true")
    vv = subprocess.run(["maestro", "--version"], env=env, capture_output=True, text=True).stdout.strip().splitlines()[-1]
    if vv != ver: say("WRONG MAESTRO %s for %s: skip" % (vv, name)); RES.append({"run": name, "skipped": "maestro is " + vv}); return
    if platform == "ios":
        toml = '[ios]\napp = "%s/app/Crossfit Tracker.app"\nbundle_id = "me.manulorenzo.crossfittracker"\nflow = "%s/work/flow.ios.yaml"\nruntime = "com.apple.CoreSimulator.SimRuntime.iOS-26-4"\nout = "out"\n' % (A, A)
    else:
        toml = '[android]\napk = "%s/app/androidApp-debug.apk"\npackage = "me.manulorenzo.crossfittracker.android.debug"\nflow = "%s/work/flow.android.yaml"\navd = "shotfleet_android"\nout = "out"\n' % (A, A)
    open(d + "/shotfleet.toml", "w").write(toml)
    pre = "load %s | swap %s | pressure %s" % (load(), swap(), pressure()); say("%s start: %s" % (name, pre)); t = time.time()
    p = subprocess.Popen(["python3", A + "/src/shotfleet.py", "run", d + "/shotfleet.toml", "--platform", platform], cwd=d, env=env, stdout=open(d + "/run.log", "w"), stderr=subprocess.STDOUT, start_new_session=True)
    try: rc = p.wait(timeout=30 * 60)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGTERM); time.sleep(20)
        try: os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        rc = 124
    wall = int(time.time() - t); txt = open(d + "/run.log").read()
    r = {"run": name, "maestro": vv, "rc": rc, "wall_s": wall, "pre": pre, "post": "load %s | swap %s | pressure %s" % (load(), swap(), pressure()),
         "captured": re.findall(r"captured (\d+/\d+) locales in (\d+)s on (\d+) (?:simulators|emulators)", txt), "retries": re.findall(r"retrying[^\n]*", txt),
         "booting": re.findall(r"booting (\d+) (?:simulators|emulators)[^\n]*", txt), "pressure_notes": re.findall(r"(?:memory pressure|short of memory)[^\n]*", txt)[:2],
         "problems": re.findall(r"checked \d+ screenshots in \d+ languages?: [^\n]*", txt), "fails": re.findall(r"^FAIL[^\n]*", txt, re.M)[:6]}
    for f in glob.glob(d + "/out*/**/*.json", recursive=True) + glob.glob(d + "/out*/**/*.html", recursive=True):
        if os.path.getsize(f) < 3_000_000: shutil.copy(f, d + "/" + os.path.relpath(f, d).replace("/", "__"))
    shutil.rmtree(d + "/out", ignore_errors=True)  # the PNGs are not evidence here; json/html/logs are kept
    say("%s done: %s" % (name, json.dumps({k: r[k] for k in ("rc", "wall_s", "captured", "retries", "booting")}))); RES.append(r); time.sleep(20)
try:
    for plat, ver in (("ios", "2.0.10"), ("ios", "2.11.0"), ("android", "2.11.0"), ("android", "2.0.10")):
        if time.time() - T0 > 80 * 60: say("over 80 min: stop"); break
        one(plat, ver)
finally:
    left = [l for l in sh("xcrun simctl list devices booted").splitlines() if "shotfleet-" in l and "(Booted)" in l]
    for l in left:
        u = re.search(r"\(([0-9A-F-]{36})\)", l)
        if u: sh("xcrun simctl shutdown " + u.group(1), 90)
    for e in re.findall(r"^(emulator-57\d\d)", sh(os.path.expanduser("~/Library/Android/sdk/platform-tools/adb") + " devices"), re.M): sh(os.path.expanduser("~/Library/Android/sdk/platform-tools/adb") + " -s %s emu kill" % e, 60)
    open(OUT + "/summary.json", "w").write(json.dumps(RES, indent=1)); say("done, elapsed %d s" % (time.time() - T0))
