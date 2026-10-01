#!/usr/bin/env python3
"""shotfleet: localized store screenshots from one Maestro flow, on parallel simulators/emulators.

usage: shotfleet doctor
       shotfleet init <App.app | app.apk> [dir]
       shotfleet run <config.toml> [--locales de,ja] [--parallel N]
       shotfleet check <out_dir>
       shotfleet export <out_dir> --fastlane <fastlane_dir>

For each language the app ships, shotfleet rewrites the flow's English text selectors into that
language using the strings compiled into the app, runs every language in parallel, and verifies
every screenshot (shows that language's strings, isn't a copy of another, none missing).
"""
import hashlib, json, os, re, shutil, subprocess, sys, time, tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSION = "0.1.0"

class Fail(Exception):
    """A user-facing error: printed as one line, no traceback."""

REQUIRED = {"ios": ("app", "bundle_id", "flow"), "android": ("apk", "package", "flow")}

def load_config(config_path):
    """(platform, cfg, path resolver) with every mistake reported as a Fail that says how to fix it."""
    cfg_path = Path(config_path).expanduser().resolve()
    if not cfg_path.is_file():
        raise Fail(f"no config at {cfg_path}. Create one with: shotfleet init <App.app | app.apk>")
    try:
        doc = tomllib.loads(cfg_path.read_text())
    except tomllib.TOMLDecodeError as e:
        raise Fail(f"{cfg_path.name} isn't valid TOML: {e}")
    platforms = [k for k in ("ios", "android") if k in doc]
    if len(platforms) != 1:
        raise Fail(f"{cfg_path.name} needs exactly one [ios] or [android] section (use one config file per platform)")
    platform = platforms[0]
    cfg = doc[platform]
    missing = [k for k in REQUIRED[platform] if not cfg.get(k)]
    if missing:
        raise Fail(f"[{platform}] in {cfg_path.name} is missing: {', '.join(missing)}")
    path = lambda p: cfg_path.parent / Path(p).expanduser()  # absolute/~ paths win, others are relative to the config
    flow = path(cfg["flow"])
    if not flow.is_file():
        raise Fail(f"flow file not found: {flow}")
    if platform == "ios":
        app = path(cfg["app"])
        if not (app / "Info.plist").is_file():
            raise Fail(f"no simulator app at {app}. Build it for the simulator (Debug-iphonesimulator) and point 'app' at the .app")
        real = sh(["/usr/libexec/PlistBuddy", "-c", "Print CFBundleIdentifier", str(app / "Info.plist")]).stdout.strip()
        if real and real != cfg["bundle_id"]:
            raise Fail(f"bundle_id is {cfg['bundle_id']} but {app.name} is {real}")
    else:
        apk = path(cfg["apk"])
        if not apk.is_file():
            raise Fail(f"no APK at {apk}")
        m = re.search(r"package: name='([^']+)'", sh([aapt2(), "dump", "badging", str(apk)]).stdout)
        if m and m.group(1) != cfg["package"]:
            raise Fail(f"package is {cfg['package']} but the APK is {m.group(1)}")
    if not shutil.which("maestro"):
        raise Fail("Maestro isn't installed. Install it with: curl -Ls https://get.maestro.mobile.dev | bash")
    return platform, cfg, path
# lproj code -> App Store Connect / fastlane locale
STORE_LOCALE = {
    "en": "en-US", "ar": "ar-SA", "da": "da", "de": "de-DE", "es": "es-ES", "fr": "fr-FR", "hi": "hi",
    "it": "it", "ja": "ja", "ko": "ko", "nb": "no", "nl": "nl-NL", "pl": "pl", "pt": "pt-BR", "ru": "ru",
    "sv": "sv", "tr": "tr", "zh-Hans": "zh-Hans", "zh-Hant": "zh-Hant", "uk": "uk", "id": "id", "ro": "ro",
}
# lproj code -> language NLLanguageRecognizer reports (differs only for these)
EXPECTED_LANG = {"nb": "nb", "zh-Hans": "zh-Hans", "zh-Hant": "zh-Hant"}
SELECTOR_KEYS = ("tapOn", "doubleTapOn", "longPressOn", "assertVisible", "assertNotVisible",
                 "scrollUntilVisible", "text", "copyTextFrom", "visible", "notVisible")

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def aapt2():
    """Newest aapt2 in the Android SDK; Fail with the fix if there is none."""
    found = sorted((SDK / "build-tools").glob("*/aapt2"))
    if not found:
        raise Fail(f"aapt2 not found under {SDK}/build-tools. Install Build-Tools in Android Studio's SDK Manager (or set ANDROID_HOME)")
    return str(found[-1])

# ---------- strings ----------

def load_strings(res_dir):
    """{lproj: {key: value}} from every *.strings file in every *.lproj under res_dir."""
    out = {}
    for lproj in sorted(Path(res_dir).glob("*.lproj")):
        if lproj.stem == "Base": continue  # Base.lproj is layout/fallback storage, not a language
        table = {}
        for f in lproj.glob("*.strings"):
            r = sh(["plutil", "-convert", "json", "-o", "-", str(f)])
            if r.returncode == 0:
                table.update(json.loads(r.stdout))
        if table:
            out[lproj.stem] = table
    return out

LOCALE_QUALIFIER = re.compile(r"^(?:([a-z]{2,3})(?:-r([A-Z]{2}))?|b\+([a-z]{2,3})((?:\+[A-Za-z0-9]+)*))$")

def android_locale(q):
    """aapt2 config qualifier -> BCP-47 tag ('de', 'pt-rBR' -> 'pt-BR', 'b+zh+Hans' -> 'zh-Hans'); None if not a pure locale."""
    m = LOCALE_QUALIFIER.match(q)
    if not m: return None
    if m.group(3): return m.group(3) + m.group(4).replace("+", "-")
    return m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")

def load_strings_apk(apk, base="en"):
    """{locale: {name: value}} from the string resources compiled into an APK (default config -> base)."""
    r = sh([aapt2(), "dump", "resources", str(apk)])
    if r.returncode != 0: raise RuntimeError(f"aapt2 dump failed: {r.stderr.strip()}")
    out, name = {}, None
    for line in r.stdout.splitlines():
        if m := re.match(r"\s*resource 0x[0-9a-f]+ string/(\S+)", line):
            name = m.group(1); continue
        if name and (m := re.match(r'\s*\(([^)]*)\) "(.*)"\s*$', line)):
            loc = base if m.group(1) == "" else android_locale(m.group(1))
            if loc:  # skip night/land/v31 and other non-locale variants
                out.setdefault(loc, {})[name] = m.group(2).replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n")
        elif not line.startswith("      "):
            name = None
    return out

def shipped_locales(strings, base="en", min_coverage=0.5):
    """Locales the app itself is translated into.

    Library resources (AndroidX, Material, Play Services) bring their own strings translated into ~80
    locales. Counting raw coverage breaks for apps with few strings of their own: an English-only app
    with 240 strings looks "translated" into 86 languages. So first separate the app's own strings
    (translated into fewer locales than the libraries' near-universal set), then measure coverage of those."""
    others = [lp for lp in strings if lp != base]
    counts = {k: sum(k in strings[lp] for lp in others) for k in strings[base]}
    top = max(counts.values(), default=0)
    own = {k for k, c in counts.items() if c < 0.9 * top} if top else set(counts)
    if len(own) < 0.1 * len(counts):  # nearly everything is universal: the app itself is translated everywhere
        own = set(counts)
    return sorted([base] + [lp for lp in others
                            if own and sum(k in strings[lp] for k in own) >= min_coverage * len(own)])

def yaml_single_quote(s):
    return "'" + s.replace("'", "''") + "'"

def regex_literal(s):
    # Maestro matches text selectors as a full Java regex; escape metacharacters
    return re.sub(r"([\\.^$|?*+()\[\]{}])", r"\\\1", s)

SELECTOR_RE = re.compile(r"^(\s*-?\s*(?:%s):\s*)(.+?)\s*$" % "|".join(SELECTOR_KEYS))

def translate_flow(flow, base, target):
    """Rewrite English text selectors to the target language. Returns (flow, untranslated selectors)."""
    by_text = {}
    for k, v in base.items():
        by_text.setdefault(v, []).append(k)
    targets = target if isinstance(target, list) else [target]  # several: match any of their translations
    missing, lines, collisions = [], [], []
    for line in flow.splitlines():
        m = SELECTOR_RE.match(line)
        if not m:
            lines.append(line); continue
        prefix, raw = m.groups()
        if raw.startswith(("{", "[", "&", "*")):  # map form continues on following lines (text: ...)
            lines.append(line); continue
        text = raw[1:-1] if raw[:1] in "'\"" and raw[-1:] == raw[:1] else raw
        keys = by_text.get(text)
        if not keys:
            missing.append(text); lines.append(line); continue
        cands = sorted({tg.get(k, text) for tg in targets for k in keys})
        if cands == [text] and regex_literal(text) == text:
            lines.append(line); continue
        # same word, different meaning on the same screen (tr: Next = Advanced = "İleri") -> a tap can hit the wrong one
        for tg in targets:
            for k in keys:
                t = tg.get(k, text)
                # likely on the same screen: same key family (iOS onboarding_*), or another short label like "Advanced"
                clash = sorted({base[o] for o, v in tg.items()
                                if v == t and o in base and base[o].casefold() != text.casefold()
                                and (o.split("_")[0] == k.split("_")[0] or len(base[o].split()) <= 2)})
                if clash: collisions.append(f"{text!r} -> {t!r} also means {', '.join(map(repr, clash))}")
        # one English label can map to several keys ("Next" -> Weiter / Nächste): match any of them
        pattern = "|".join(map(regex_literal, cands))
        pattern = pattern if len(cands) == 1 else f"({pattern})"
        lines.append(prefix + yaml_single_quote(pattern))
    return "\n".join(lines) + "\n", sorted(set(missing)), sorted(set(collisions))

def redirect_screenshot(lines, shots_dir):
    """Rewrite one flow line if it names a screenshot, so files land in shots_dir. Handles the scalar
    form ('- takeScreenshot: 01_home') and the map form ('- takeScreenshot:' then '    path: 01_home')."""
    line = lines[-1]
    if m := re.match(r"^(\s*- takeScreenshot:\s*)['\"]?([^'\"]+?)['\"]?\s*$", line):
        lines[-1] = f"{m.group(1)}{yaml_single_quote(str(shots_dir / m.group(2)))}"
    elif (m := re.match(r"^(\s*path:\s*)['\"]?([^'\"]+?)['\"]?\s*$", line)) and len(lines) > 1 \
            and re.match(r"^\s*- takeScreenshot:\s*$", lines[-2]):
        lines[-1] = f"{m.group(1)}{yaml_single_quote(str(shots_dir / m.group(2)))}"

def print_untranslated(report):
    miss = sorted({m for v in report["locales"].values() for m in v["untranslated_selectors"]})
    if miss:
        print("selectors not found in the app's strings (left as-is; they may fail outside English):")
        for m in miss: print(f"   {m!r}")

def print_result(lp, r, expected):
    print(f"{'ok  ' if r['ok'] else 'FAIL'} {lp:8} {r['screenshots']}/{expected} screenshots"
          + (" (retried)" if r.get("retried") or r.get("attempts", 1) > 1 else "")
          + ("" if r["ok"] else f"  {r.get('error') or ''}"[:160]))

def count_screenshots(flow):
    return len(re.findall(r"(?m)^\s*- takeScreenshot:", flow))

def localize_flow(flow, lproj, shots_dir):
    """Make a translated flow self-contained for one locale.

    Maestro can only run several simulators at once from one process (--shard-split), which hands
    any flow to any device. So the language travels with the flow, as launch arguments, not with
    the simulator.
    """
    locale = STORE_LOCALE.get(lproj, lproj).replace("-", "_")  # number/date formats follow the store locale
    args = [f'      AppleLanguages: "({lproj})"', f'      AppleLocale: "{locale}"']
    launch = lambda clear: ["- launchApp:"] + (["    clearState: true"] if clear else []) + ["    arguments:"] + args
    header, sep, body = flow.partition("\n---\n")
    if not sep:
        raise ValueError("flow needs an 'appId:' header followed by '---'")
    header = re.sub(r"(?m)^name:.*\n?", "", header).rstrip() + f"\nname: {lproj}"
    out = launch(clear=True)  # fresh state per locale: onboarding runs every time
    for line in body.splitlines():
        if re.match(r"^\s*- launchApp\s*$", line):
            out += launch(clear=False)
        elif re.match(r"^\s*- launchApp:", line):
            raise ValueError("launchApp with options isn't supported yet; use a bare '- launchApp'")
        else:
            out.append(line); redirect_screenshot(out, shots_dir)
    return header + "\n---\n" + "\n".join(out) + "\n"

# ---------- simulators ----------

class Sim:
    def __init__(self, udid): self.udid = udid
    def run(self, *args, check=True):
        r = sh(["xcrun", "simctl", *args])
        if check and r.returncode != 0:
            raise RuntimeError(f"simctl {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout

def make_pool(n, device_type, runtime, prefix="shotfleet"):
    """Reuse or create n simulators named <prefix>-<i>, boot them, clean the status bar."""
    existing = json.loads(sh(["xcrun", "simctl", "list", "devices", "-j"]).stdout)["devices"].get(runtime, [])
    by_name = {d["name"]: d for d in existing if d.get("isAvailable")}
    pool = []
    for i in range(n):
        name = f"{prefix}-{i + 1}"
        udid = by_name[name]["udid"] if name in by_name else \
            sh(["xcrun", "simctl", "create", name, device_type, runtime]).stdout.strip()
        if not udid:
            raise RuntimeError(f"could not create simulator {name} ({device_type}, {runtime})")
        s = Sim(udid)
        s.run("boot", udid, check=False)  # already-booted is fine
        pool.append(s)
    for s in pool:
        s.run("bootstatus", s.udid, "-b")
        s.run("status_bar", s.udid, "override", "--time", "9:41", "--dataNetwork", "wifi", "--wifiMode", "active",
              "--wifiBars", "3", "--cellularMode", "active", "--cellularBars", "4",
              "--batteryState", "charged", "--batteryLevel", "100")
    return pool

# ---------- host safety ----------

def descendants(root):
    """PIDs under root (inclusive), from one ps snapshot."""
    kids = {}
    for line in sh(["ps", "-Ao", "pid=,ppid="]).stdout.splitlines():
        pid, ppid = map(int, line.split())
        kids.setdefault(ppid, []).append(pid)
    out, todo = set(), [root]
    while todo:
        p = todo.pop(); out.add(p); todo += kids.get(p, [])
    return out

def run_guarded(cmd, timeout, env=None):
    """subprocess.run, plus a watchdog that kills `simctl diagnose` started under this command.
    Maestro dumps simulator diagnostics after every failed flow; several at once wedge CoreSimulator
    (even `simctl list` hangs). shotfleet keeps Maestro's own screenshots and logs, so they aren't needed."""
    import threading
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    done = threading.Event()
    def watch():
        while not done.wait(5):
            ours = descendants(proc.pid)
            for line in sh(["pgrep", "-f", "simctl diagnose"]).stdout.split():
                if int(line) in ours: sh(["kill", "-9", line])
    threading.Thread(target=watch, daemon=True).start()
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        for p in descendants(proc.pid): sh(["kill", "-9", str(p)])
        raise
    finally:
        done.set()
    return subprocess.CompletedProcess(cmd, proc.returncode, out, "")

def fit_parallel(n):
    """Halve parallelism under memory pressure; refuse when critical. A loaded Mac makes flows time out
    and retries pile on more load."""
    level = sh(["sysctl", "-n", "kern.memorystatus_vm_pressure_level"]).stdout.strip()
    if level == "4":
        raise Fail("macOS reports critical memory pressure. Close some apps and run again")
    if level == "2" and n > 1:
        print(f"memory pressure is elevated: using {max(1, n // 2)} devices instead of {n}")
        return max(1, n // 2)
    return n

# ---------- run ----------

OUR_SIMS = set()  # UDIDs of shotfleet's simulators, so cleanup never touches anyone else's

def kill_stale_drivers():
    """Kill Maestro iOS drivers attached to shotfleet's simulators. A driver left over from an earlier run
    keeps port 7001 bound to *its* simulator, and the next run then silently drives the wrong device.
    Drivers for other simulators (other projects, other terminals) are left alone."""
    if not OUR_SIMS: return
    for pid in sh(["pgrep", "-f", "xcodebuild test-without-building"]).stdout.split():
        args = sh(["ps", "-o", "args=", "-p", pid]).stdout
        if "maestro" in args and any(u in args for u in OUR_SIMS):
            sh(["kill", pid])

def junit_results(path):
    import xml.etree.ElementTree as ET
    if not path.exists(): return {}
    res = {}
    for tc in ET.parse(path).iter("testcase"):
        fail = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
        res[tc.get("name")] = {"ok": fail is None, "seconds": round(float(tc.get("time") or 0)),
                               "error": (fail.get("message") or fail.text or "").strip()[:300] if fail is not None else None}
    return res

def cmd_run(config_path, only=None, parallel=None):
    platform, cfg, path = load_config(config_path)
    if platform == "android":
        out = path(cfg.get("out", "out")).resolve(); out.mkdir(parents=True, exist_ok=True)
        return android_run(cfg, path, out, only, parallel)
    cfg.setdefault("device_type", "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max")
    cfg.setdefault("runtime", latest_ios_runtime())
    cfg["app"] = str(path(cfg["app"]))
    # default: the strings compiled into the app under test, so selectors always match the binary
    strings = load_strings(path(cfg["strings"]) if "strings" in cfg else Path(cfg["app"]))
    flow = path(cfg["flow"]).read_text()
    base_locale = cfg.get("base_locale", "en")
    if base_locale not in strings:
        raise Fail(f"the app has no {base_locale} strings. Set base_locale in the config to the language your flow is written in")
    en = strings[base_locale]
    locales = only or cfg.get("locales") or sorted(strings)
    out = path(cfg.get("out", "out")).resolve()
    # stale flows, logs and JUnit files from an earlier run must never be read as this run's results;
    # raw/<locale> is cleared per locale below, so a partial rerun keeps the other languages
    for d in ("flows", "debug"): shutil.rmtree(out / d, ignore_errors=True)
    for f in out.glob("junit*.xml"): f.unlink()
    (out / "flows").mkdir(parents=True)

    # translate every flow first, so selector problems show up before any simulator boots
    report = {"locales": {}}
    for lp in locales:
        if lp not in strings:
            print(f"skip {lp}: app has no {lp}.lproj"); continue
        text, missing, clash = translate_flow(flow, en, strings[lp])
        for c in clash: print(f"warning {lp}: {c}; anchor that step (below:/above:) if it taps the wrong element")
        shutil.rmtree(out / "raw" / lp, ignore_errors=True); (out / "raw" / lp).mkdir(parents=True)
        (out / "flows" / f"{lp}.yaml").write_text(localize_flow(text, lp, out / "raw" / lp))
        report["locales"][lp] = {"untranslated_selectors": missing}
    print_untranslated(report)

    if not report["locales"]:
        raise Fail(f"none of those languages are in the app. It ships: {', '.join(sorted(strings))}")
    n = fit_parallel(min(parallel or cfg.get("parallel", 4), len(report["locales"])))
    print(f"booting {n} simulators ({cfg['device_type'].split('.')[-1]}, {cfg['runtime'].split('.')[-1]})")
    pool = make_pool(n, cfg["device_type"], cfg["runtime"])
    OUR_SIMS.update(s.udid for s in pool)
    kill_stale_drivers()
    for sim in pool:  # install once; each flow's clearState gives every locale a fresh start
        sim.run("terminate", sim.udid, cfg["bundle_id"], check=False)
        sim.run("uninstall", sim.udid, cfg["bundle_id"], check=False)
        sim.run("install", sim.udid, cfg["app"])

    expected = count_screenshots(flow)

    def batch(lps, attempt):
        """Run these locales in one sharded Maestro process; return {lproj: result}."""
        flows_dir = out / "flows" / f"attempt{attempt}"
        flows_dir.mkdir(parents=True)
        for lp in lps: shutil.copy(out / "flows" / f"{lp}.yaml", flows_dir)
        k = min(n, len(lps))
        junit = out / f"junit{attempt}.xml"; junit.unlink(missing_ok=True)
        env = {**os.environ, "MAESTRO_DRIVER_STARTUP_TIMEOUT": "240000", "MAESTRO_CLI_NO_ANALYTICS": "1"}  # 4 drivers starting at once are slow
        try:
            r = run_guarded(["maestro", "--device", ",".join(s.udid for s in pool[:k]), "test", str(flows_dir),
                             "--shard-split", str(k), "--format", "JUNIT", "--output", str(junit),
                             "--debug-output", str(out / "debug" / f"attempt{attempt}")],
                            env=env, timeout=cfg.get("timeout_s", 600) * -(-len(lps) // k) + 300)
            (out / f"maestro{attempt}.log").write_text(r.stdout + r.stderr)
        except subprocess.TimeoutExpired:
            print("maestro timed out")
        finally:
            kill_stale_drivers()
        res = junit_results(junit)
        out_ = {}
        for lp in lps:
            shots = len(list((out / "raw" / lp).glob("*.png")))
            # Maestro skips its report when a shard crashes; the screenshots on disk are the ground truth then
            r_ = res.get(lp) or {"ok": shots == expected, "error": None if shots == expected else "no result (see maestro log)"}
            if r_["ok"] and shots != expected:
                r_ = {**r_, "ok": False, "error": f"flow passed but took {shots} of {expected} screenshots"}
            out_[lp] = {**r_, "ok": r_["ok"] and shots == expected, "screenshots": shots, "attempts": attempt}
        return out_

    print(f"capturing {len(report['locales'])} locales on {n} simulators...", flush=True)
    t0 = time.time()
    final = batch(list(report["locales"]), 1)
    retry = [lp for lp, r_ in final.items() if not r_["ok"]]
    if retry:  # simulators and drivers flake; one retry of just the failures is cheap
        print(f"retrying {len(retry)}: {', '.join(retry)}", flush=True)
        for lp in retry: shutil.rmtree(out / "raw" / lp); (out / "raw" / lp).mkdir()
        final.update(batch(retry, 2))
    results = []
    for lp, r_ in final.items():
        print_result(lp, r_, expected)
        results.append({"lproj": lp, **r_})
    for r in results: report["locales"][r["lproj"]].update(r)
    report["wall_seconds"] = round(time.time() - t0)
    report["simulators"] = n
    report["app"] = cfg["app"]
    (out / "run.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"captured {sum(r['ok'] for r in results)}/{len(results)} locales in {report['wall_seconds']}s on {n} simulators")
    failed = [r["lproj"] for r in results if not r["ok"]]
    return max(cmd_check(out, strings), 1 if failed else 0)

# ---------- android ----------

SDK = Path(os.environ.get("ANDROID_HOME", Path.home() / "Library/Android/sdk"))
DEMO_MODE = [  # SystemUI demo mode: fixed clock, full battery and signal, no notification icons
    "settings put global sysui_demo_allowed 1",
    "am broadcast -a com.android.systemui.demo -e command enter",
    "am broadcast -a com.android.systemui.demo -e command clock -e hhmm 0941",
    "am broadcast -a com.android.systemui.demo -e command battery -e level 100 -e plugged false",
    "am broadcast -a com.android.systemui.demo -e command network -e wifi show -e level 4 -e fully true",
    "am broadcast -a com.android.systemui.demo -e command network -e mobile show -e datatype none -e level 4",
    "am broadcast -a com.android.systemui.demo -e command notifications -e visible false",
]

class Emu:
    def __init__(self, port): self.port, self.serial = port, f"emulator-{port}"
    def adb(self, *args, check=True, timeout=180):
        r = sh(["adb", "-s", self.serial, *args], timeout=timeout)
        if check and r.returncode != 0:
            raise RuntimeError(f"adb {' '.join(args)}: {(r.stderr or r.stdout).strip()}")
        return r.stdout
    def booted(self):
        return sh(["adb", "-s", self.serial, "shell", "getprop", "sys.boot_completed"], timeout=15).stdout.strip() == "1"

def start_emu(avd, port, read_only=True):
    return subprocess.Popen([str(SDK / "emulator/emulator"), "-avd", avd, "-port", str(port), "-no-window", "-no-audio",
                             "-no-boot-anim", "-no-snapshot"] + (["-read-only"] if read_only else []),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def wait_booted(emus, timeout=600):
    t0 = time.time()
    while not all(e.booted() for e in emus):
        if time.time() - t0 > timeout: raise RuntimeError("emulators did not boot in time")
        time.sleep(3)

def android_pool(n, cfg, pool):
    """Boot n read-only copies of one AVD (created on first use as a 1080x1920 phone) into `pool`.
    The caller owns `pool` and kills it in a finally, so emulators never outlive a failed boot."""
    avd = cfg.get("avd", "shotfleet_android")
    avd_dir = Path.home() / ".android/avd" / f"{avd}.avd"
    if not avd_dir.exists():
        image = cfg.get("system_image", "system-images;android-36;google_apis;arm64-v8a")
        r = sh([str(SDK / "cmdline-tools/latest/bin/avdmanager"), "create", "avd", "-n", avd, "-k", image, "-d", "pixel_5"], input="no\n")
        if r.returncode != 0 or not (avd_dir / "config.ini").exists():
            raise Fail(f"couldn't create the emulator {avd} from {image}: {(r.stderr or r.stdout).strip()[-300:]}. "
                       f"Install that system image in Android Studio's SDK Manager, or set system_image in the config")
        ini = avd_dir / "config.ini"
        ini.write_text(re.sub(r"(?m)^hw\.lcd\.width=.*", "hw.lcd.width=1080",
                       re.sub(r"(?m)^hw\.lcd\.height=.*", "hw.lcd.height=1920",
                       re.sub(r"(?m)^hw\.lcd\.density=.*", "hw.lcd.density=420", ini.read_text()))))
    if not (avd_dir / "userdata-qemu.img").exists():  # one-time first boot, writable, so copies boot fast
        e = Emu(5700); p = start_emu(avd, e.port, read_only=False)
        wait_booted([e]); time.sleep(20); e.adb("shell", "reboot", "-p", check=False); p.wait(timeout=120)
    for i in range(n):
        e = Emu(5702 + 2 * i)
        if e.booted(): raise Fail(f"{e.serial} is already running. Stop it (adb -s {e.serial} emu kill) and run again")
        start_emu(avd, e.port); pool.append(e)
        time.sleep(2)  # staggered starts avoid adb port races
    wait_booted(pool)
    for e in pool:
        for c in DEMO_MODE: e.adb("shell", c, check=False)

def android_flow(text, name, shots_dir):
    """Per-run copy of a translated flow: own name, own screenshot folder, starts with a plain launchApp.
    No clearState: on Android it wipes the per-app language shotfleet just set; shotfleet clears data itself."""
    header, sep, body = text.partition("\n---\n")
    if not sep: raise ValueError("flow needs an 'appId:' header followed by '---'")
    header = re.sub(r"(?m)^name:.*\n?", "", header).rstrip() + f"\nname: {name}"
    out = [] if re.match(r"\s*- launchApp", body.lstrip("\n")) else ["- launchApp"]
    for line in body.splitlines():
        if re.match(r"^\s*clearState:", line): continue
        out.append(line); redirect_screenshot(out, shots_dir)
    return header + "\n---\n" + "\n".join(out) + "\n"

def flow_devices(debug_dir):
    """{flow file stem: device serial} from Maestro's own log of how it sharded the run."""
    m = {}
    for log in Path(debug_dir).rglob("maestro.log"):
        for dev, flows in re.findall(r"Selected device (\S+) using port \d+ with execution plan "
                                     r"ExecutionPlan\(flowsToRun=\[([^\]]*)\]", log.read_text(errors="replace")):
            for f in flows.split(","):
                if f.strip(): m[Path(f.strip()).stem] = dev
    return m

def android_run(cfg, path, out, only, parallel):
    apk, pkg = str(path(cfg["apk"])), cfg["package"]
    strings = load_strings_apk(apk, cfg.get("base_locale", "en"))
    base = strings[cfg.get("base_locale", "en")]
    locales = only or cfg.get("locales") or shipped_locales(strings)
    flow = path(cfg["flow"]).read_text()
    expected = count_screenshots(flow)
    # stale flows, logs and JUnit files from an earlier run must never be read as this run's results
    for d in ("flows", "tmp", "debug"): shutil.rmtree(out / d, ignore_errors=True)
    for f in out.glob("junit*.xml"): f.unlink()
    report = {"locales": {}}
    for lp in locales:
        if lp not in strings: print(f"skip {lp}: app has no {lp} strings"); continue
        _, missing, clash = translate_flow(flow, base, strings[lp])
        for c in clash: print(f"warning {lp}: {c}; anchor that step (below:/above:) if it taps the wrong element")
        report["locales"][lp] = {"untranslated_selectors": missing}
    print_untranslated(report)
    todo = list(report["locales"])
    if not todo:
        raise Fail(f"none of those languages are in the app. It ships: {', '.join(shipped_locales(strings))}")
    n = fit_parallel(min(parallel or cfg.get("parallel", 4), len(todo)))
    print(f"booting {n} emulators ({cfg.get('avd', 'shotfleet_android')}, 1080x1920)", flush=True)
    pool = []
    try:
        android_pool(n, cfg, pool)
        for e in pool: e.adb("install", "-r", "-g", apk)

        def round_(lps, tag):
            """One locale per emulator. Maestro shards the identical flows across devices in an order we
            don't control; its log says which flow ran where, and each device's language is known."""
            lang = {}
            for e, lp in zip(pool, lps):
                e.adb("shell", "pm", "clear", pkg)  # fresh onboarding; also resets the app language, so set it after
                e.adb("shell", "cmd", "locale", "set-app-locales", pkg, "--locales", lp)
                for c in DEMO_MODE: e.adb("shell", c, check=False)  # re-assert: SystemUI can drop it after boot
                lang[e.serial] = lp
            text, _, _ = translate_flow(flow, base, [strings[lp] for lp in lps])
            fdir = out / "flows" / tag; fdir.mkdir(parents=True)
            for j in range(len(lps)):
                (fdir / f"{tag}_f{j}.yaml").write_text(android_flow(text, f"{tag}_f{j}", out / "tmp" / tag / f"f{j}"))
            junit, dbg = out / f"junit_{tag}.xml", out / "debug" / tag
            junit.unlink(missing_ok=True); shutil.rmtree(dbg, ignore_errors=True)
            try:
                r = run_guarded(["maestro", "--device", ",".join(e.serial for e in pool[:len(lps)]), "test", str(fdir),
                                 "--shard-split", str(len(lps)), "--format", "JUNIT", "--output", str(junit), "--debug-output", str(dbg)],
                                timeout=cfg.get("timeout_s", 600) + 300, env={**os.environ, "MAESTRO_CLI_NO_ANALYTICS": "1"})
                (out / f"maestro_{tag}.log").write_text(r.stdout + r.stderr)
            except subprocess.TimeoutExpired:
                print(f"maestro timed out in {tag}")
            ran_on, res, results = flow_devices(dbg), junit_results(junit), {}
            for j in range(len(lps)):
                fname, dev = f"{tag}_f{j}", ran_on.get(f"{tag}_f{j}")
                if dev not in lang: continue
                lp = lang[dev]
                dst = out / "raw" / lp
                shutil.rmtree(dst, ignore_errors=True)
                src = out / "tmp" / tag / f"f{j}"
                if src.exists(): shutil.move(str(src), dst)
                else: dst.mkdir(parents=True)
                shots = len(list(dst.glob("*.png")))
                r_ = res.get(fname) or {"ok": shots == expected, "error": None if shots == expected else "no result"}
                results[lp] = {**r_, "ok": r_["ok"] and shots == expected, "screenshots": shots, "device": dev}
            for lp in lps:
                results.setdefault(lp, {"ok": False, "error": "flow never ran (see maestro log)", "screenshots": 0})
            return results

        t0, final = time.time(), {}
        print(f"capturing {len(todo)} locales on {n} emulators, {-(-len(todo) // n)} rounds...", flush=True)
        for i in range(0, len(todo), n):
            final.update(round_(todo[i:i + n], f"r{i // n + 1}"))
        retry = [lp for lp, r_ in final.items() if not r_["ok"]]
        if retry:
            print(f"retrying {len(retry)}: {', '.join(retry)}", flush=True)
            for i in range(0, len(retry), n):
                for lp, r_ in round_(retry[i:i + n], f"retry{i // n + 1}").items(): final[lp] = {**r_, "retried": True}
    finally:
        for e in pool: e.adb("emu", "kill", check=False)
    for lp in todo:
        r_ = final[lp]
        print_result(lp, r_, expected)
        report["locales"][lp].update(r_)
    report.update(wall_seconds=round(time.time() - t0), emulators=n, platform="android", apk=apk)
    (out / "run.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"captured {sum(r_['ok'] for r_ in final.values())}/{len(todo)} locales in {report['wall_seconds']}s on {n} emulators")
    return max(cmd_check(out, strings), 0 if all(r_["ok"] for r_ in final.values()) else 1)

# ---------- check ----------

def ocr_tool():
    exe = HERE / ".build" / "ocr"
    src = HERE / "ocr.swift"
    if not exe.exists() or exe.stat().st_mtime < src.stat().st_mtime:
        exe.parent.mkdir(exist_ok=True)
        r = sh(["swiftc", "-O", str(src), "-o", str(exe)])
        if r.returncode != 0: raise RuntimeError("ocr build failed:\n" + r.stderr)
    return str(exe)

def judge_screen(lp, ocr, tables):
    """(locale the screen shows, problem or None) for one screenshot's OCR result.

    Scores each locale by how many recognized lines are exactly one of its strings: generic language
    detection is unreliable on short UI labels (it reads Russian tab bars as Kazakh)."""
    lines = {l.strip() for l in ocr.get("text", "").splitlines() if len(l.strip()) > 1}
    score = {o: len(lines & vals) for o, vals in tables.items()}
    best = max(score.values(), default=0)
    got = lp if score.get(lp, 0) == best else max(score, key=score.get)
    if not ocr.get("chars"):
        return got, "no text found (blank or still loading?)"
    if best == 0:  # nothing matched the app's strings; fall back to language detection
        want = EXPECTED_LANG.get(lp, lp.split("-")[0])
        if ocr.get("lang") != want and ocr.get("langs", {}).get(want, 0) < 0.2:
            return ocr.get("lang"), f"text looks like '{ocr.get('lang')}', expected '{want}'"
        return lp, None
    if got != lp:
        return got, f"shows {got} strings ({score[got]} lines) more than {lp} ({score.get(lp, 0)})"
    return got, None

def cmd_check(out, strings=None):
    """Verify screenshots: each shows its own locale's strings, and no image is repeated across languages."""
    out = Path(out)
    if strings is None and (out / "run.json").exists():
        run = json.loads((out / "run.json").read_text())
        strings = load_strings_apk(run["apk"]) if run.get("platform") == "android" else load_strings(Path(run["app"]))
    tables = {lp: set(t.values()) for lp, t in (strings or {}).items()}
    raw = out / "raw"
    ocr = ocr_tool()
    rows, by_hash, problems = [], {}, []
    if not raw.is_dir() or not any(raw.glob("*/*.png")):
        print("no screenshots to check"); return 1
    pngs = [png for lp_dir in sorted(p for p in raw.iterdir() if p.is_dir()) for png in sorted(lp_dir.glob("*.png"))]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:  # each OCR is its own process
        ocrs = list(ex.map(lambda png: json.loads(sh([ocr, str(png)]).stdout or "{}"), pngs))
    for png, r in zip(pngs, ocrs):
        lp = png.parent.name
        h = hashlib.sha256(png.read_bytes()).hexdigest()[:12]
        by_hash.setdefault(h, []).append(f"{lp}/{png.name}")
        got, problem = judge_screen(lp, r, tables)
        if problem: problems.append(f"{lp}/{png.name}: {problem}")
        rows.append({"file": f"{lp}/{png.name}", "sha": h, "lang": got, "chars": r.get("chars", 0)})
    for h, files in by_hash.items():
        langs = {f.split("/")[0] for f in files}
        if len(langs) > 1:
            problems.append(f"identical image in {len(langs)} languages: {', '.join(files)}")
    # expected screenshot set = union across locales; flag locales missing any
    names = {r["file"].split("/")[1] for r in rows}
    for lp_dir in sorted(p for p in raw.iterdir() if p.is_dir()):
        have = {p.name for p in lp_dir.glob("*.png")}
        if have != names:
            problems.append(f"{lp_dir.name}: missing {', '.join(sorted(names - have))}")
    (out / "check.json").write_text(json.dumps({"screenshots": rows, "problems": problems}, indent=1, ensure_ascii=False))
    write_gallery(out, rows, problems)
    print(f"\nchecked {len(rows)} screenshots: {len(problems)} problem(s)")
    for p in problems: print(f"  - {p}")
    return 1 if problems else 0

def write_gallery(out, rows, problems):
    """out/index.html: one row per locale, one column per screen; flagged screenshots outlined in red."""
    import html
    flagged = {p.split(":")[0] for p in problems}
    for p in problems:  # "identical image in N languages: a/x.png, b/x.png"
        if p.startswith("identical image"): flagged.update(f.strip() for f in p.split(":", 1)[1].split(","))
    names = sorted({r["file"].split("/")[1] for r in rows})
    locales = sorted({r["file"].split("/")[0] for r in rows} | {p.split(":")[0] for p in problems if ":" in p and "/" not in p.split(":")[0] and " " not in p.split(":")[0]})
    cells = []
    for lp in locales:
        tds = []
        for nm in names:
            f = f"{lp}/{nm}"
            if (out / "raw" / f).exists():
                bad = f in flagged
                tds.append(f'<td><a href="raw/{f}"><img src="raw/{f}" loading="lazy" class="{"bad" if bad else ""}"></a></td>')
            else:
                tds.append('<td class="missing">missing</td>')
        cells.append(f"<tr><th>{html.escape(lp)}</th>{''.join(tds)}</tr>")
    probs = "".join(f"<li>{html.escape(p)}</li>" for p in problems) or "<li>none</li>"
    (out / "index.html").write_text(f"""<!doctype html><meta charset="utf-8"><title>shotfleet results</title>
<style>body{{font:14px -apple-system,sans-serif;margin:16px;background:#fafafa}}table{{border-collapse:collapse}}
th{{text-align:right;padding-right:8px;vertical-align:middle}}td{{padding:3px}}img{{width:120px;border:3px solid transparent;border-radius:6px}}
img.bad{{border-color:#d33}}td.missing{{width:120px;height:260px;background:#fee;color:#d33;text-align:center}}</style>
<h1>shotfleet: {len(rows)} screenshots, {len(locales)} locales</h1><h3>Problems ({len(problems)})</h3><ul>{probs}</ul>
<table><tr><th></th>{''.join(f"<th>{html.escape(n)}</th>" for n in names)}</tr>{''.join(cells)}</table>""")

# ---------- doctor / init / export ----------

def cmd_doctor():
    """Check the tools shotfleet drives; print how to fix what's missing."""
    have = lambda c: shutil.which(c) is not None
    has_aapt2 = bool(sorted((SDK / "build-tools").glob("*/aapt2")))
    checks = [
        ("maestro", have("maestro"), "curl -Ls https://get.maestro.mobile.dev | bash", "both"),
        ("swiftc (OCR checks)", have("swiftc"), "xcode-select --install", "both"),
        ("xcrun simctl", sh(["xcrun", "simctl", "help"]).returncode == 0 if have("xcrun") else False,
         "install Xcode and an iOS Simulator runtime", "iOS"),
        ("adb", have("adb"), "Android Studio > SDK Manager > Platform-Tools", "Android"),
        ("emulator", (SDK / "emulator/emulator").exists(), f"SDK Manager > Android Emulator (ANDROID_HOME={SDK})", "Android"),
        ("avdmanager", (SDK / "cmdline-tools/latest/bin/avdmanager").exists(), "SDK Manager > Command-line Tools", "Android"),
        ("aapt2", has_aapt2, "SDK Manager > Build-Tools", "Android"),
    ]
    for name, ok, fix, platform in checks:
        print(f"{'ok  ' if ok else 'MISSING'} {name:20} ({platform})" + ("" if ok else f"  -> {fix}"))
    ok_ios = all(ok for _, ok, _, p in checks if p in ("both", "iOS"))
    ok_android = all(ok for _, ok, _, p in checks if p in ("both", "Android"))
    print(f"\niOS: {'ready' if ok_ios else 'not ready'}   Android: {'ready' if ok_android else 'not ready'}")
    return 0 if ok_ios or ok_android else 1

FLOW_TEMPLATE = """appId: {app_id}
name: "Store screenshots"
---
# Write this flow in English: shotfleet translates every text selector for each language.
# Tap and assert by the text the user sees; take a screenshot for each store image you want.
- launchApp
- waitForAnimationToEnd:
    timeout: 5000
- takeScreenshot: 01_home
# - tapOn: "Settings"
# - takeScreenshot: 02_settings
"""

def cmd_init(app, dest="."):
    """Write shotfleet.toml + flow.yaml for an .app (iOS simulator build) or .apk."""
    app, dest = Path(app).expanduser().resolve(), Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    if app.suffix == ".apk":
        if not app.is_file(): raise Fail(f"no APK at {app}")
        m = re.search(r"package: name='([^']+)'", sh([aapt2(), "dump", "badging", str(app)]).stdout)
        if not m: raise Fail(f"{app.name} doesn't look like a valid APK (aapt2 couldn't read its package name)")
        app_id = m.group(1)
        locales = shipped_locales(load_strings_apk(app))
        cfg = f'[android]\napk = "{app}"\npackage = "{app_id}"\nflow = "flow.yaml"\nparallel = 4\nout = "out"\n'
    elif app.suffix == ".app":
        if not (app / "Info.plist").is_file(): raise Fail(f"no simulator app at {app}")
        app_id = sh(["/usr/libexec/PlistBuddy", "-c", "Print CFBundleIdentifier", str(app / "Info.plist")]).stdout.strip()
        locales = sorted(load_strings(app))
        cfg = (f'[ios]\napp = "{app}"\nbundle_id = "{app_id}"\nflow = "flow.yaml"\n'
               'device_type = "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max"   # 1320x2868 = App Store 6.9"\n'
               f'runtime = "{latest_ios_runtime()}"\nparallel = 4\nout = "out"\n')
    else:
        print("pass a simulator .app or an .apk"); return 2
    for name, text in (("shotfleet.toml", cfg), ("flow.yaml", FLOW_TEMPLATE.format(app_id=app_id))):
        if (dest / name).exists(): print(f"keeping existing {dest / name}"); continue
        (dest / name).write_text(text); print(f"wrote {dest / name}")
    print(f"{app_id}: {len(locales)} languages ({', '.join(locales)})")
    print(f"next: edit {dest / 'flow.yaml'}, then: shotfleet run {dest / 'shotfleet.toml'} --locales en")
    return 0

def latest_ios_runtime():
    rts = json.loads(sh(["xcrun", "simctl", "list", "runtimes", "-j"]).stdout or '{"runtimes": []}')["runtimes"]
    ios = [r for r in rts if r.get("platform") == "iOS" and r.get("isAvailable")]
    return ios[-1]["identifier"] if ios else "com.apple.CoreSimulator.SimRuntime.iOS-26-5"

# Android language tag -> Google Play listing locale (fastlane supply folder names)
PLAY_LOCALE = {
    "en": "en-US", "ar": "ar", "da": "da-DK", "de": "de-DE", "es": "es-ES", "fr": "fr-FR", "hi": "hi-IN",
    "it": "it-IT", "ja": "ja-JP", "ko": "ko-KR", "nb": "no-NO", "nl": "nl-NL", "pl": "pl-PL", "pt": "pt-BR",
    "pt-BR": "pt-BR", "pt-PT": "pt-PT", "ru": "ru-RU", "sv": "sv-SE", "tr": "tr-TR", "zh-CN": "zh-CN",
    "zh-TW": "zh-TW", "uk": "uk", "id": "id", "in": "id", "ro": "ro", "fi": "fi-FI", "cs": "cs-CZ",
}

def cmd_export(out, fastlane):
    """Copy verified screenshots into fastlane's upload folders (deliver for iOS, supply for Android).
    Locales with a failed check are skipped, so a bad screenshot can't reach a store listing."""
    out, fastlane = Path(out), Path(fastlane)
    if not (out / "run.json").is_file():
        raise Fail(f"no shotfleet run in {out}. Run 'shotfleet run <config>' first")
    run = json.loads((out / "run.json").read_text())
    android = run.get("platform") == "android"
    problems = json.loads((out / "check.json").read_text())["problems"] if (out / "check.json").exists() else []
    bad = {p.split(":")[0].split("/")[0] for p in problems if not p.startswith("identical")}
    for p in problems:
        if p.startswith("identical"): bad.update(f.strip().split("/")[0] for f in p.split(":", 1)[1].split(","))
    done = []
    for lp_dir in sorted(d for d in (out / "raw").iterdir() if d.is_dir()):
        lp = lp_dir.name
        if lp in bad: print(f"skip {lp}: failed checks (see {out / 'check.json'})"); continue
        store = (PLAY_LOCALE if android else STORE_LOCALE).get(lp, lp)
        dst = fastlane / "metadata/android" / store / "images/phoneScreenshots" if android else fastlane / "screenshots" / store
        dst.mkdir(parents=True, exist_ok=True)
        for old in dst.glob("*.png"): old.unlink()  # replace the set, don't mix old and new
        for png in sorted(lp_dir.glob("*.png")): shutil.copy2(png, dst / png.name)
        done.append(store)
    print(f"exported {len(done)} locales to {fastlane}: {', '.join(done)}")
    return 0 if not bad else 1

def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="shotfleet", description="Localized App Store and Google Play screenshots from one English Maestro flow.")
    ap.add_argument("--version", action="version", version=f"shotfleet {VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")
    sub.add_parser("doctor", help="check that Maestro, Xcode and the Android SDK are ready")
    p = sub.add_parser("init", help="write a starter config and flow for an app")
    p.add_argument("app", help="simulator .app or .apk"); p.add_argument("dir", nargs="?", default=".", help="where to write them (default: here)")
    p = sub.add_parser("run", help="capture every language and check the screenshots")
    p.add_argument("config", help="shotfleet.toml")
    p.add_argument("--locales", help="only these languages, comma-separated (e.g. de,ja)")
    p.add_argument("--parallel", type=int, help="how many simulators or emulators to use (default: the config's, or 4)")
    p = sub.add_parser("check", help="check an existing run's screenshots again")
    p.add_argument("out", help="the run's output folder")
    p = sub.add_parser("export", help="copy screenshots that passed into fastlane's folders")
    p.add_argument("out", help="the run's output folder"); p.add_argument("--fastlane", required=True, help="your fastlane folder")
    a = ap.parse_args(argv)
    if a.cmd == "run" and a.parallel is not None and a.parallel < 1:
        ap.error("--parallel must be 1 or more")
    try:
        if a.cmd == "doctor": return cmd_doctor()
        if a.cmd == "init": return cmd_init(a.app, a.dir)
        if a.cmd == "run": return cmd_run(a.config, a.locales.split(",") if a.locales else None, a.parallel)
        if a.cmd == "check":
            if not Path(a.out).is_dir(): raise Fail(f"no folder at {a.out}")
            return cmd_check(a.out)
        if a.cmd == "export": return cmd_export(a.out, a.fastlane)
    except (Fail, RuntimeError) as e:  # RuntimeError: simctl/adb/aapt2 failures, already worded for people
        print(f"shotfleet: {e}", file=sys.stderr); return 2
    except KeyboardInterrupt:
        kill_stale_drivers()
        print("\nshotfleet: stopped. Simulators and emulators may still be running.", file=sys.stderr); return 130

if __name__ == "__main__":
    sys.exit(main())
