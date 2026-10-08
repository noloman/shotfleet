#!/usr/bin/env python3
"""Guide re-check on Maestro 2.11.0 (marketing/articles/02 verify items 1-8) with the two fixture apps. Assumes the device lock is held.
Own devices only: one private iPhone simulator 'guide-recheck-iphone' and two read-only emulators on ports 5760/5762. Hard cap 55 min; every call has a timeout."""
import os, subprocess, time, signal, json, glob, shutil, re, sys
G = "/Users/manu/Developer/shotfleet-rc-build/guide-recheck-2.11.0"
OUT = G + "/out-" + time.strftime("%Y%m%d-%H%M%S"); os.makedirs(OUT)
M = os.path.expanduser("~/.maestro-tests/2.11.0/bin/maestro"); SDK = os.path.expanduser("~/Library/Android/sdk"); ADB = SDK + "/platform-tools/adb"
ENV = dict(os.environ, JAVA_OPTS="-Duser.home=" + G + "/home", MAESTRO_CLI_NO_ANALYTICS="1", MAESTRO_DISABLE_UPDATE_CHECK="true")
T0 = time.time(); LOG = open(OUT + "/job.log", "a"); RES = {}
def say(m): LOG.write(time.strftime("%H:%M:%S ") + m + "\n"); LOG.flush()
def over(): return time.time() - T0 > 55 * 60
def run(cmd, t=300, cwd=None, name=None, env=ENV):
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try: out, _ = p.communicate(timeout=t); rc = p.returncode
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGTERM); time.sleep(5)
        try: os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        out, _ = p.communicate(); rc = 124; out += "\n[killed after %d s]" % t
    if name: open(OUT + "/" + name + ".log", "w").write(" ".join(cmd) + "\n" + out)
    return rc, out
def pngs(since, roots):
    r = []
    for root in roots:
        for f in glob.glob(root + "/**/*.png", recursive=True):
            if os.path.getmtime(f) >= since: r.append(f.replace(G + "/", ""))
    return sorted(r)
def keep(files, label):
    d = OUT + "/png-" + label; os.makedirs(d, exist_ok=True)
    for f in files:
        shutil.copy(G + "/" + f, d + "/" + f.replace("/", "__"))
def put(path, text): os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "w").write(text)

def ios():
    sim = None
    try:
        rc, out = run(["xcrun", "simctl", "create", "guide-recheck-iphone", "com.apple.CoreSimulator.SimDeviceType.iPhone-17", "com.apple.CoreSimulator.SimRuntime.iOS-26-4"], 60)
        sim = out.strip().splitlines()[-1]; say("sim " + sim); RES["ios_sim"] = sim
        say("boot rc %s" % run(["xcrun", "simctl", "boot", sim], 120)[0]); say("bootstatus rc %s" % run(["xcrun", "simctl", "bootstatus", sim, "-b"], 300)[0])
        say("install rc %s" % run(["xcrun", "simctl", "install", sim, G + "/ios/FleetFixture.app"], 120)[0])
        F = OUT + "/ios/flows"
        head = "appId: dev.shotfleet.fixture\n"
        launch = "- launchApp:\n    clearState: true\n    arguments:\n      AppleLanguages: \"(${APP_LANG})\"\n      AppleLocale: \"${APP_LOCALE}\"\n"
        body = "- waitForAnimationToEnd:\n    timeout: 5000\n- takeScreenshot: shots/${APP_LANG}/01_welcome\n- tapOn: \"${NEXT}\"\n- waitForAnimationToEnd:\n    timeout: 5000\n- takeScreenshot: shots/${APP_LANG}/02_settings\n"
        put(F + "/guide.yaml", head + "---\n" + launch + body)
        put(F + "/header-default.yaml", head + "env:\n  APP_LANG: en\n  APP_LOCALE: en_US\n---\n" + launch + "- waitForAnimationToEnd:\n    timeout: 5000\n- takeScreenshot: t1/${APP_LANG}_welcome\n")
        put(F + "/race.yaml", head + "---\n" + launch + "- takeScreenshot: race/${APP_LANG}_straight_after_launch\n")
        put(F + "/platform.yaml", head + "---\n- launchApp\n- runFlow:\n    when:\n      platform: iOS\n    commands:\n      - takeScreenshot: plat/ios_block\n- runFlow:\n    when:\n      platform: Android\n    commands:\n      - takeScreenshot: plat/android_block\n")
        RES["ios"] = {}
        for lang, loc, nxt in (("en", "en_US", "Next"), ("de", "de_DE", "Weiter"), ("ja", "ja_JP", "次へ")):
            if over(): break
            d = OUT + "/ios/loop"; os.makedirs(d, exist_ok=True); t = time.time()
            rc, out = run([M, "--device", sim, "test", "-e", "APP_LANG=" + lang, "-e", "APP_LOCALE=" + loc, "-e", "NEXT=" + nxt, F + "/guide.yaml"], 300, d, "ios-loop-" + lang)
            found = pngs(t, [d, G + "/home/.maestro/tests"]); keep(found, "loop-" + lang); RES["ios"]["loop-" + lang] = {"rc": rc, "pngs": found}
        for name, args in (("header-default", ["-e", "APP_LANG=de", "-e", "APP_LOCALE=de_DE"]), ("race", ["-e", "APP_LANG=de", "-e", "APP_LOCALE=de_DE"]), ("platform", [])):
            if over(): break
            d = OUT + "/ios/" + name; os.makedirs(d, exist_ok=True); t = time.time()
            rc, out = run([M, "--device", sim, "test"] + args + [F + "/%s.yaml" % name], 300, d, "ios-" + name)
            found = pngs(t, [d, G + "/home/.maestro/tests"]); keep(found, name); RES["ios"][name] = {"rc": rc, "pngs": found}
        rc, out = run([M, "--device", sim, "-e", "APP_LANG=de", "test", F + "/guide.yaml"], 120, OUT, "ios-trap2-e-before-test")
        RES["ios"]["trap2"] = {"rc": rc, "first": out.strip().splitlines()[:3]}
        rc, out = run([M, "--version"], 60); RES["maestro_version"] = out.strip().splitlines()[-1]
    finally:
        if sim:
            run(["xcrun", "simctl", "shutdown", sim], 90); say("deleted my sim rc %s" % run(["xcrun", "simctl", "delete", sim], 90)[0])

def adbs(p, *a, t=60): return run([ADB, "-s", "emulator-%d" % p] + list(a), t)
def android():
    pids = []; ports = (5760, 5762); RES["android"] = {}; A = RES["android"]
    try:
        for p in ports:
            if subprocess.run("%s devices | grep -q emulator-%d" % (ADB, p), shell=True).returncode == 0: say("port %d already in use: abort android" % p); return
        for p in ports:
            pids.append(subprocess.Popen([SDK + "/emulator/emulator", "-avd", "shotfleet_android", "-port", str(p), "-no-window", "-no-audio", "-no-boot-anim", "-snapshot", "shotfleet", "-no-snapshot-save", "-read-only"], stdout=open(OUT + "/emu-%d.log" % p, "w"), stderr=subprocess.STDOUT, start_new_session=True))
        for p in ports:
            for i in range(120):
                if adbs(p, "shell", "getprop", "sys.boot_completed")[1].strip() == "1": break
                time.sleep(3)
            say("emulator-%d booted after ~%d s" % (p, i * 3)); say("install %s" % adbs(p, "install", "-r", "-g", G + "/android/FleetFixture.apk", t=180)[1].strip()[-40:])
        P = 5760; pkg = "com.shotfleet.fixture"; F = OUT + "/android/flows"
        head = "appId: com.shotfleet.fixture\n"
        flow = head + "---\n- launchApp\n- waitForAnimationToEnd:\n    timeout: 5000\n- takeScreenshot: shots/${APP_LANG}/01_welcome\n- tapOn: \"${NEXT}\"\n- waitForAnimationToEnd:\n    timeout: 5000\n- takeScreenshot: shots/${APP_LANG}/02_settings\n"
        put(F + "/guide.yaml", flow); put(F + "/clearstate.yaml", flow.replace("- launchApp\n", "- launchApp:\n    clearState: true\n"))
        put(F + "/platform.yaml", head + "---\n- launchApp\n- runFlow:\n    when:\n      platform: iOS\n    commands:\n      - takeScreenshot: plat/ios_block\n- runFlow:\n    when:\n      platform: Android\n    commands:\n      - takeScreenshot: plat/android_block\n")
        def loc(p): return adbs(p, "shell", "cmd", "locale", "get-app-locales", pkg)[1].strip().splitlines()[-1]
        def setde(p): adbs(p, "shell", "pm", "clear", pkg); adbs(p, "shell", "cmd", "locale", "set-app-locales", pkg, "--locales", "de")
        setde(P); A["after_set_de"] = loc(P)
        t = time.time(); d = OUT + "/android/b"; os.makedirs(d, exist_ok=True)
        rc, out = run([M, "--device", "emulator-%d" % P, "test", "-e", "APP_LANG=de", "-e", "NEXT=Weiter", F + "/guide.yaml"], 300, d, "android-b-no-clearstate")
        f = pngs(t, [d, G + "/home/.maestro/tests"]); keep(f, "android-b"); A["no_clearState"] = {"rc": rc, "locales_after": loc(P), "pngs": f}
        setde(P); t = time.time(); d = OUT + "/android/c"; os.makedirs(d, exist_ok=True)
        rc, out = run([M, "--device", "emulator-%d" % P, "test", "-e", "APP_LANG=de", "-e", "NEXT=Weiter", F + "/clearstate.yaml"], 300, d, "android-c-clearstate")
        f = pngs(t, [d, G + "/home/.maestro/tests"]); keep(f, "android-c"); A["clearState"] = {"rc": rc, "locales_after": loc(P), "pngs": f}
        setde(P); adbs(P, "shell", "pm", "clear", pkg); A["pm_clear_after_set_de"] = loc(P)
        t = time.time(); d = OUT + "/android/p"; os.makedirs(d, exist_ok=True)
        rc, out = run([M, "--device", "emulator-%d" % P, "test", F + "/platform.yaml"], 300, d, "android-platform")
        f = pngs(t, [d, G + "/home/.maestro/tests"]); keep(f, "android-platform"); A["platform"] = {"rc": rc, "pngs": f}
        A["parallel"] = []
        for attempt in (1, 2):
            if over(): break
            for p in ports: setde(p)
            t = time.time(); procs = []
            for p in ports:
                d = OUT + "/android/par%d-%d" % (attempt, p); os.makedirs(d, exist_ok=True)
                procs.append((p, d, subprocess.Popen([M, "--device", "emulator-%d" % p, "test", "-e", "APP_LANG=de", "-e", "NEXT=Weiter", F + "/guide.yaml"], cwd=d, env=ENV, stdout=open(OUT + "/android-par%d-%d.log" % (attempt, p), "w"), stderr=subprocess.STDOUT, start_new_session=True)))
            time.sleep(10); lsof = run(["sh", "-c", "lsof -nP -iTCP:7001 -sTCP:LISTEN | tail -n +2 | wc -l; lsof -nP -iTCP -sTCP:LISTEN | grep -c java"], 30)[1].strip()
            r = {}
            for p, d, pr in procs:
                try: rc = pr.wait(timeout=240)
                except subprocess.TimeoutExpired:
                    os.killpg(pr.pid, signal.SIGKILL); rc = 124
                txt = open(OUT + "/android-par%d-%d.log" % (attempt, p)).read()
                r[p] = {"rc": rc, "TimeoutException": "TimeoutException" in txt, "NoSuchFileException": "NoSuchFileException" in txt, "pngs": pngs(t, [d])}
            A["parallel"].append({"attempt": attempt, "listen7001_java_at_10s": lsof, "procs": r})
    finally:
        for p in ports: adbs(p, "emu", "kill", t=30)
        time.sleep(10)
        for pr in pids:
            try: os.killpg(pr.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError): pass

try: ios(); android()
finally:
    RES["elapsed_s"] = int(time.time() - T0); open(OUT + "/summary.json", "w").write(json.dumps(RES, indent=1)); say("done " + json.dumps(RES)[:300])
