#!/usr/bin/env python3
"""shotfleet: localized store screenshots from one Maestro flow, on parallel iOS simulators.

usage: shotfleet.py run <config.toml> [--locales de,ja] [--parallel N]
       shotfleet.py check <out_dir>

For each locale the app ships (*.lproj), shotfleet rewrites the flow's English text selectors
into that language using the app's own .strings files, runs it on a simulator whose app
language is set to that locale, and verifies every screenshot (right language, not a copy).
"""
import hashlib, json, os, re, shutil, subprocess, sys, time, tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
# lproj code -> App Store Connect / fastlane locale
STORE_LOCALE = {
    "en": "en-US", "ar": "ar-SA", "da": "da", "de": "de-DE", "es": "es-ES", "fr": "fr-FR", "hi": "hi",
    "it": "it", "ja": "ja", "ko": "ko", "nb": "no", "nl": "nl-NL", "pl": "pl", "pt": "pt-BR", "ru": "ru",
    "sv": "sv", "tr": "tr", "zh-Hans": "zh-Hans", "zh-Hant": "zh-Hant", "uk": "uk", "id": "id", "ro": "ro",
}
# lproj code -> language NLLanguageRecognizer reports (differs only for these)
EXPECTED_LANG = {"nb": "nb", "zh-Hans": "zh-Hans", "zh-Hant": "zh-Hant"}
SELECTOR_KEYS = ("tapOn", "doubleTapOn", "longPressOn", "assertVisible", "assertNotVisible",
                 "scrollUntilVisible", "text", "copyTextFrom")

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

# ---------- strings ----------

def load_strings(res_dir):
    """{lproj: {key: value}} from every *.strings file in every *.lproj under res_dir."""
    out = {}
    for lproj in sorted(Path(res_dir).glob("*.lproj")):
        table = {}
        for f in lproj.glob("*.strings"):
            r = sh(["plutil", "-convert", "json", "-o", "-", str(f)])
            if r.returncode == 0:
                table.update(json.loads(r.stdout))
        if table:
            out[lproj.stem] = table
    return out

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
        cands = sorted({target.get(k, text) for k in keys})
        if cands == [text] and regex_literal(text) == text:
            lines.append(line); continue
        # same word, different meaning on the same screen (tr: Next = Advanced = "İleri") -> a tap can hit the wrong one
        for k in keys:
            t = target.get(k, text)
            clash = sorted({base[o] for o, v in target.items()
                            if v == t and base.get(o, t) != text and o.split("_")[0] == k.split("_")[0]})
            if clash: collisions.append(f"{text!r} -> {t!r} also means {', '.join(map(repr, clash))}")
        # one English label can map to several keys ("Next" -> Weiter / Nächste): match any of them
        pattern = "|".join(map(regex_literal, cands))
        pattern = pattern if len(cands) == 1 else f"({pattern})"
        lines.append(prefix + yaml_single_quote(pattern))
    return "\n".join(lines) + "\n", sorted(set(missing)), sorted(set(collisions))

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
        elif m := re.match(r"^(\s*- takeScreenshot:\s*)['\"]?([^'\"]+?)['\"]?\s*$", line):
            out.append(f"{m.group(1)}{yaml_single_quote(str(shots_dir / m.group(2)))}")
        else:
            out.append(line)
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

# ---------- run ----------

def kill_stale_drivers():
    # a Maestro iOS driver left over from an earlier run keeps port 7001 bound to *its* simulator,
    # and the next run then silently drives the wrong device
    sh(["pkill", "-f", "xcodebuild test-without-building.*maestro"])

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
    cfg_path = Path(config_path).resolve()
    cfg = tomllib.loads(cfg_path.read_text())["ios"]
    path = lambda p: cfg_path.parent / Path(p).expanduser()  # absolute/~ paths win, others are relative to the config
    cfg["app"] = str(path(cfg["app"]))
    # default: the strings compiled into the app under test, so selectors always match the binary
    strings = load_strings(path(cfg["strings"]) if "strings" in cfg else Path(cfg["app"]))
    flow = path(cfg["flow"]).read_text()
    en = strings[cfg.get("base_locale", "en")]
    locales = only or cfg.get("locales") or sorted(strings)
    out = path(cfg.get("out", "out")).resolve()
    shutil.rmtree(out / "flows", ignore_errors=True)  # raw/<locale> is cleared per locale below, so a partial rerun keeps the rest
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
    miss = sorted({m for v in report["locales"].values() for m in v["untranslated_selectors"]})
    if miss:
        print("selectors not found in the app's strings (left as-is; they may fail outside English):")
        for m in miss: print(f"   {m!r}")

    n = min(parallel or cfg.get("parallel", 4), len(report["locales"]))
    print(f"booting {n} simulators ({cfg['device_type'].split('.')[-1]}, {cfg['runtime'].split('.')[-1]})")
    kill_stale_drivers()
    pool = make_pool(n, cfg["device_type"], cfg["runtime"])
    for sim in pool:  # install once; each flow's clearState gives every locale a fresh start
        sim.run("terminate", sim.udid, cfg["bundle_id"], check=False)
        sim.run("uninstall", sim.udid, cfg["bundle_id"], check=False)
        sim.run("install", sim.udid, cfg["app"])

    expected = len(re.findall(r"(?m)^\s*- takeScreenshot:", flow))

    def batch(lps, attempt):
        """Run these locales in one sharded Maestro process; return {lproj: result}."""
        flows_dir = out / "flows" / f"attempt{attempt}"
        flows_dir.mkdir(parents=True)
        for lp in lps: shutil.copy(out / "flows" / f"{lp}.yaml", flows_dir)
        k = min(n, len(lps))
        junit = out / f"junit{attempt}.xml"
        env = {**os.environ, "MAESTRO_DRIVER_STARTUP_TIMEOUT": "240000"}  # 4 drivers starting at once are slow
        try:
            r = sh(["maestro", "--device", ",".join(s.udid for s in pool[:k]), "test", str(flows_dir),
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
            out_[lp] = {**r_, "screenshots": shots, "attempts": attempt}
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
        print(f"{'ok  ' if r_['ok'] else 'FAIL'} {lp:8} {r_['screenshots']}/{expected} screenshots"
              + (" (retried)" if r_["attempts"] > 1 else "") + ("" if r_["ok"] else f"  {r_.get('error') or ''}"[:160]))
        results.append({"lproj": lp, **r_})
    for r in results: report["locales"][r["lproj"]].update(r)
    report["wall_seconds"] = round(time.time() - t0)
    report["simulators"] = n
    report["app"] = cfg["app"]
    (out / "run.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"captured {sum(r['ok'] for r in results)}/{len(results)} locales in {report['wall_seconds']}s on {n} simulators")
    failed = [r["lproj"] for r in results if not r["ok"]]
    return max(cmd_check(out, strings), 1 if failed else 0)

# ---------- check ----------

def ocr_tool():
    exe = HERE / ".build" / "ocr"
    src = HERE / "ocr.swift"
    if not exe.exists() or exe.stat().st_mtime < src.stat().st_mtime:
        exe.parent.mkdir(exist_ok=True)
        r = sh(["swiftc", "-O", str(src), "-o", str(exe)])
        if r.returncode != 0: raise RuntimeError("ocr build failed:\n" + r.stderr)
    return str(exe)

def cmd_check(out, strings=None):
    """Verify screenshots: each shows its own locale's strings, and no image is repeated across languages."""
    out = Path(out)
    if strings is None and (out / "run.json").exists():
        strings = load_strings(Path(json.loads((out / "run.json").read_text())["app"]))
    tables = {lp: set(t.values()) for lp, t in (strings or {}).items()}
    raw = out / "raw"
    ocr = ocr_tool()
    rows, by_hash, problems = [], {}, []
    if not raw.is_dir() or not any(raw.glob("*/*.png")):
        print("no screenshots to check"); return 1
    for lp_dir in sorted(p for p in raw.iterdir() if p.is_dir()):
        lp = lp_dir.name
        for png in sorted(lp_dir.glob("*.png")):
            data = png.read_bytes()
            h = hashlib.sha256(data).hexdigest()[:12]
            by_hash.setdefault(h, []).append(f"{lp}/{png.name}")
            r = json.loads(sh([ocr, str(png)]).stdout or "{}")
            # which locale's strings does this screen actually show? (generic language detection is
            # unreliable on short UI labels: it reads Russian tab bars as Kazakh)
            lines = {l.strip() for l in r.get("text", "").splitlines() if len(l.strip()) > 1}
            score = {o: len(lines & vals) for o, vals in tables.items()}
            best = max(score.values(), default=0)
            got = lp if score.get(lp, 0) == best else max(score, key=score.get)
            if not r.get("chars"):
                problems.append(f"{lp}/{png.name}: no text found (blank or still loading?)")
            elif best == 0:  # nothing matched the app's strings; fall back to language detection
                want = EXPECTED_LANG.get(lp, lp.split("-")[0])
                if r.get("lang") != want and r.get("langs", {}).get(want, 0) < 0.2:
                    problems.append(f"{lp}/{png.name}: text looks like '{r.get('lang')}', expected '{want}'")
            elif got != lp:
                problems.append(f"{lp}/{png.name}: shows {got} strings ({score[got]} lines) more than {lp} ({score.get(lp, 0)})")
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

def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "run":
        opts = dict(zip(a[2::2], a[3::2]))
        only = opts.get("--locales", "").split(",") if "--locales" in opts else None
        sys.exit(cmd_run(a[1], only, int(opts["--parallel"]) if "--parallel" in opts else None))
    if len(a) == 2 and a[0] == "check":
        sys.exit(cmd_check(a[1]))
    print(__doc__); sys.exit(2)

if __name__ == "__main__":
    main()
