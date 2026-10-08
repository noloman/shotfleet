#!/usr/bin/env python3
# Build chain for the obytes showcase, rebuild from upstream commit fd9b358 (v9.0.0-10-gfd9b358). Usage: chain.py STAGE [STAGE...]  (stops at first failure)
# stages: clone pnpm_tool install prebuild pod ios_build android_build
import os, sys, time, subprocess, signal, threading, datetime, shlex

S = "/Users/manu/Developer/shotfleet-rc-build/showcase-obytes"
SRC = S + "/src"
LOGS = S + "/logs-fd9b358"
HOME = os.path.expanduser("~")
PLOG = S + "/progress.log"

def ts(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def plog(msg):
    with open(PLOG, "a") as f: f.write(f"{ts()} {msg}\n")
    print(f"{ts()} {msg}", flush=True)

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def disk_free_gib(): return int(sh("/bin/df -g /Users/manu | tail -1").split()[3])
def load1(): return float(sh("sysctl -n vm.loadavg").strip("{} ").split()[0])
def free_pct(): return int(sh("memory_pressure | grep 'free percentage'").split()[-1].strip("%"))
def pressure(): return int(sh("sysctl -n kern.memorystatus_vm_pressure_level"))
def swapouts(): return int(sh("vm_stat | grep -i swapouts").split()[-1].strip("."))
def swap_rate(secs=60):
    a = swapouts(); time.sleep(secs); return swapouts() - a

def metrics(tag):
    sr = swap_rate(60)
    m = dict(disk=disk_free_gib(), load=load1(), free=free_pct(), pr=pressure(), swapouts60=sr)
    plog(f"METRICS {tag}: disk_free_GiB={m['disk']} load1={m['load']} free_mem%={m['free']} vm_pressure_level={m['pr']} swapouts_per_60s={m['swapouts60']}")
    return m

def gate(name):
    plog(f"GATE {name}: start (disk>=30, load<100, free>=40%, pressure<=2, swapouts<2000/60s; poll 2 min, up to 60 min)")
    t0 = time.time(); n = 0
    while time.time() - t0 < 3600:
        n += 1
        sr = swap_rate(60)
        m = dict(disk=disk_free_gib(), load=load1(), free=free_pct(), pr=pressure(), sr=sr)
        ok = m["disk"] >= 30 and m["load"] < 100 and m["free"] >= 40 and m["pr"] <= 2 and sr < 2000
        plog(f"GATE {name} try {n}: disk={m['disk']} load1={m['load']} free%={m['free']} pr={m['pr']} swapouts/60s={sr} -> {'PASS' if ok else 'wait'}")
        if ok: return True
        time.sleep(60)
    plog(f"GATE {name}: TIMEOUT after 60 min, not started")
    return False

BASE_ENV = dict(os.environ)
BASE_ENV.update({
    "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8", "CI": "1", "EXPO_NO_TELEMETRY": "1", "HUSKY": "0",
    "COCOAPODS_DISABLE_STATS": "1",
    "PATH": f"{S}/tools/node_modules/.bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:{HOME}/.sdkman/candidates/java/17.0.5-tem/bin",
    "PNPM_HOME": S + "/pnpm-home",
    "npm_config_store_dir": S + "/pnpm-store",
    "npm_config_cache_dir": S + "/pnpm-cache",
    "XDG_CACHE_HOME": S + "/xdg-cache",
    "XDG_STATE_HOME": S + "/xdg-state",
    "EXPO_PUBLIC_APP_ENV": "development",
})
ANDROID_ENV = dict(BASE_ENV)
ANDROID_ENV.update({
    "ANDROID_HOME": HOME + "/Library/Android/sdk", "ANDROID_SDK_ROOT": HOME + "/Library/Android/sdk",
    "JAVA_HOME": HOME + "/.sdkman/candidates/java/17.0.5-tem",
})

def run_step(name, cmd, cwd, env, limit=3600, logfile=None):
    """Run cmd (list) detached in its own process group, with monitor. Returns rc (99 = pressure stop, 124 = timeout)."""
    logfile = logfile or f"{LOGS}/{name}.log"
    full = ["nice", "-n", "10", "caffeinate", "-i", "perl", "-e", f"alarm {limit}; exec @ARGV"] + cmd
    plog(f"STEP {name} START cwd={cwd} cmd={' '.join(shlex.quote(c) for c in cmd)} log={logfile}")
    metrics(f"{name} start")
    t0 = time.time()
    lf = open(logfile, "ab")
    p = subprocess.Popen(full, cwd=cwd, env=env, stdout=lf, stderr=subprocess.STDOUT, start_new_session=True)
    with open(LOGS + "/pids.txt", "a") as f: f.write(f"{ts()} {name} pid=pgid={p.pid}\n")
    with open(S + "/RESUME.md", "a") as f: f.write(f"\n- {ts()} step {name} running, pid/pgid {p.pid}, log {logfile}\n")
    plog(f"STEP {name} pid/pgid={p.pid}")
    state = {"bad": 0, "stop": False}
    def monitor():
        nxt = time.time() + 300
        while p.poll() is None and not state["stop"]:
            time.sleep(5)
            if time.time() < nxt or p.poll() is not None: continue
            nxt = time.time() + 300
            sr = swap_rate(60); fp = free_pct()
            plog(f"MONITOR {name}: disk={disk_free_gib()} load1={load1()} free%={fp} swapouts/60s={sr}")
            if disk_free_gib() < 30:
                plog(f"MONITOR {name}: disk below 30 GiB, stopping my own process group {p.pid}"); state["stop"] = True; state["why"] = "disk"
                try: os.killpg(p.pid, signal.SIGTERM)
                except Exception: pass
                return
            if sr > 20000 or fp < 20: state["bad"] += 1
            else: state["bad"] = 0
            if state["bad"] >= 2:
                plog(f"MONITOR {name}: memory pressure twice in a row, stopping my own process group {p.pid}")
                state["stop"] = True; state["why"] = "pressure"
                try: os.killpg(p.pid, signal.SIGTERM)
                except Exception: pass
                return
    th = threading.Thread(target=monitor, daemon=True); th.start()
    try:
        p.wait(timeout=limit + 60)
    except subprocess.TimeoutExpired:
        plog(f"STEP {name}: hard limit, killing my own group {p.pid}")
        try: os.killpg(p.pid, signal.SIGTERM)
        except Exception: pass
        time.sleep(5)
        try: os.killpg(p.pid, signal.SIGKILL)
        except Exception: pass
        p.wait()
    rc = p.returncode
    if state["stop"]:
        time.sleep(5)
        try: os.killpg(p.pid, signal.SIGKILL)
        except Exception: pass
        rc = 99
    elif rc == -signal.SIGALRM or rc == 142: rc = 124
    state["stop"] = True
    wall = int(time.time() - t0)
    plog(f"STEP {name} END rc={rc} wall={wall//60}m{wall%60:02d}s")
    metrics(f"{name} end")
    left = sh(f"ps -axo pid,pgid,command | awk '$2=={p.pid}' | cut -c1-120")
    if left: plog(f"STEP {name}: processes of my group still alive:\n{left}")
    return rc

def pnpm(*a): return ["pnpm", *a]

SHA = "fd9b358ed11913d2a49fd9ffa6582fe03ba130e7"
def stage(name):
    if name == "clone":
        plog("DOWNLOAD obytes/react-native-template-obytes (git clone --depth 50 + tags depth 1) from github.com, ~36 MB estimate")
        sc = (f"set -e; cd {S}; git clone --depth 50 https://github.com/obytes/react-native-template-obytes.git src; cd src; "
              f"git fetch --tags --depth 1 origin; git cat-file -e {SHA}^{{commit}}; git checkout --detach {SHA}; "
              f"test \"$(git rev-parse HEAD)\" = {SHA}; test \"$(git describe)\" = v9.0.0-10-gfd9b358; git status --short | wc -l; "
              f"git rev-parse HEAD; git describe; du -sh .git")
        return run_step(name, ["sh", "-c", sc], S, BASE_ENV, 900)
    if name == "pnpm_tool":
        plog("DOWNLOAD pnpm@10.12.3 from registry.npmjs.org (npm install --prefix tools), ~20 MB estimate")
        return run_step(name, ["npm", "install", "--prefix", S + "/tools", "--no-audit", "--no-fund", "pnpm@10.12.3"], S, BASE_ENV, 900)
    if name == "install":
        if not gate("install"): return 3
        plog("DOWNLOAD npm packages (pnpm install --frozen-lockfile, ~1300 packages) from registry.npmjs.org into pnpm-store inside showcase-obytes, estimate 0.5-1.5 GB; plus only-allow via npx (preinstall)")
        return run_step(name, pnpm("install", "--frozen-lockfile", "--network-concurrency", "4"), SRC, BASE_ENV, 3600)
    if name == "prebuild":
        e = dict(BASE_ENV); e["STRICT_ENV_VALIDATION"] = "1"
        plog("DOWNLOAD expo-template-bare-minimum tarball (expo prebuild) from registry.npmjs.org, small (<1 MB est)")
        return run_step(name, pnpm("exec", "expo", "prebuild", "--no-install"), SRC, e, 1800)
    if name == "pod":
        if not gate("pod"): return 3
        plog("DOWNLOAD CocoaPods specs + pods (pod install) from cdn.cocoapods.org, github.com, repo1.maven.org (prebuilt RN/Hermes if used), estimate 0.3-0.6 GB")
        return run_step(name, ["pod", "install"], SRC + "/ios", BASE_ENV, 3600)
    if name == "ios_build":
        if not gate("ios_build"): return 3
        cmd = ["xcodebuild", "-workspace", "ios/ObytesApp.xcworkspace", "-scheme", "ObytesApp", "-configuration", "Release",
               "-sdk", "iphonesimulator", "-derivedDataPath", "ios/build", "-jobs", "2", "ARCHS=arm64", "ONLY_ACTIVE_ARCH=YES",
               "IPHONEOS_DEPLOYMENT_TARGET=15.1", "CODE_SIGNING_ALLOWED=NO", "build"]
        return run_step(name, cmd, SRC, BASE_ENV, 3600)
    if name == "android_build":
        if not gate("android_build"): return 3
        plog("DOWNLOAD Gradle wrapper dist (services.gradle.org) + Maven Central/Google Maven/Gradle plugin portal artifacts missing from ~/.gradle, estimate 0.2-1.2 GB")
        cmd = ["./gradlew", "assembleRelease", "--no-daemon", "-Dorg.gradle.workers.max=2", "-Dorg.gradle.jvmargs=-Xmx2g",
               "-Pkotlin.compiler.execution.strategy=in-process", "-PreactNativeArchitectures=arm64-v8a"]
        e = dict(ANDROID_ENV); e["GRADLE_OPTS"] = "-Dorg.gradle.daemon=false -Dorg.gradle.workers.max=2"
        return run_step(name, cmd, SRC + "/android", e, 3600)
    raise SystemExit("unknown stage " + name)

if __name__ == "__main__":
    retries = {"prebuild": 1, "pod": 1}
    for st in sys.argv[1:]:
        rc = stage(st)
        while rc != 0 and retries.get(st, 0) > 0:
            retries[st] -= 1
            plog(f"RETRY {st} (rc={rc}); known hiccup, rerun without source edit")
            rc = stage(st)
        if rc != 0:
            plog(f"CHAIN stopped: stage {st} rc={rc}")
            with open(S + "/RESUME.md", "a") as f: f.write(f"\n- {ts()} chain stopped at {st} rc={rc}\n")
            sys.exit(rc)
    plog("CHAIN done: " + " ".join(sys.argv[1:]))
    with open(S + "/RESUME.md", "a") as f: f.write(f"\n- {ts()} chain done: {' '.join(sys.argv[1:])}\n")
