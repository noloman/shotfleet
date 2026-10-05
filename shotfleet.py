#!/usr/bin/env python3
"""shotfleet: localized store screenshots from one Maestro flow, on parallel simulators/emulators.

usage: shotfleet doctor
       shotfleet init [App.app] [app.apk] [--dir dir]   (no build given: finds the newest Debug one here)
       shotfleet run <config.toml> [--locales de,ja] [--parallel N]
       shotfleet check <folder> [--app App.app|app.apk] [--report dir] [--content [shotfleet.toml]]
       shotfleet export <out_dir> --fastlane <fastlane_dir>

For each language the app ships, shotfleet rewrites the flow's English text selectors into that
language using the strings compiled into the app, runs every language in parallel, and verifies
every screenshot (shows that language's strings, isn't a copy of another, none missing).
"""
import sys
if sys.version_info < (3, 11):
    print(f"shotfleet needs Python 3.11 or newer; this is {sys.version.split()[0]} ({sys.executable}).\n"
          "Install one (macOS: brew install python; Linux: your package manager).", file=sys.stderr)
    sys.exit(2)
import base64, contextlib, csv, functools, glob, hashlib, html, io, json, os, re, shlex, shutil, signal, socket, struct, zlib
import plistlib, platform as host_platform, ssl, subprocess, tarfile, tempfile, threading, time, tomllib, unicodedata, urllib.error, urllib.parse, urllib.request, zipfile
# everything is imported up front: a Homebrew Python upgrade mid-run deletes the old library folder (seen 2026-10-01)
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSION = "0.1.1"

class Fail(Exception):
    """A user-facing error: printed as one line, no traceback."""

# Only the build is required: everything else is read from it or defaulted. Unknown or mistyped settings are refused
# early, because a typo like `ipd = true` would otherwise cost a multi-minute run.
KEYS = {"common": {"flow": str, "out": str, "parallel": int, "locales": list, "base_locale": str, "strings": (str, list), "timeout_s": int, "stall_s": int},
        "ios": {"app": str, "bundle_id": str, "device_type": str, "device_types": list, "runtime": str, "simctl": list},
        "android": {"apk": str, "package": str, "avd": str, "avd_tablet": str, "avd_tablet-7": str, "system_image": str, "devices": list, "shell": list}}
REQUIRED = {"ios": ("app",), "android": ("apk",)}
TABLES = ("ios", "android", "hooks", "overrides", "inputs", "expect")  # the optional tables [hooks], [overrides.<locale>], [inputs] and [expect.<screenshot>] are documented in the README
EXPECT_KEYS = ("any", "all", "not")
EXAMPLE_SETUP = {"shell": '"setprop debug.myapp.demo 1"', "simctl": '"ui $UDID appearance dark"'}
HOOK_EVENTS = ("before_run", "after_run", "before_export", "after_export")

def check_tables(doc, name):
    """Refuse an unknown top-level table (a typo like [hook] would otherwise be ignored silently) and malformed hooks/overrides."""
    import difflib
    for key in doc:
        if key not in TABLES:
            near = difflib.get_close_matches(key, TABLES, n=1)
            raise Fail(f"{name} has an unknown table [{key}]" + (f"; did you mean [{near[0]}]?" if near else f". Known tables: {', '.join(TABLES)}"))
    for key, value in doc.get("hooks", {}).items():
        if key == "hook_timeout_s":
            if not isinstance(value, int) or isinstance(value, bool): raise Fail(f"[hooks] hook_timeout_s in {name} should be a whole number")
        elif key not in HOOK_EVENTS:
            import difflib as dl
            near = dl.get_close_matches(key, HOOK_EVENTS, n=1)
            raise Fail(f"[hooks] in {name} has an unknown event '{key}'" + (f"; did you mean '{near[0]}'?" if near else f". Events: {', '.join(HOOK_EVENTS)}"))
        elif not (isinstance(value, str) or isinstance(value, list) and all(isinstance(c, str) for c in value)):
            raise Fail(f"[hooks] {key} in {name} should be a command (a string) or a list of commands")
    for key, value in doc.get("inputs", {}).items():  # [inputs] name = "default"; [inputs.<locale>] name = "that language's text"
        for k, v in (value.items() if isinstance(value, dict) else [(key, value)]):
            if not isinstance(v, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k):
                raise Fail(f"[inputs] in {name}: '{k}' should be a name (letters, digits, _) set to text, e.g. name = \"Alex\" or, under [inputs.ja], name = \"田中\"")
    for locale, table in doc.get("overrides", {}).items():
        if not isinstance(table, dict) or not all(isinstance(v, str) for v in table.values()):
            raise Fail(f"[overrides.{locale}] in {name} should map English texts to text in that language, e.g. \"Next\" = \"İleri\"")
    check_expect(doc.get("expect", {}), name)

def check_expect(expect, name):
    """[expect.<screenshot>] any/all/not = ["text", ...], with [expect.<screenshot>.<locale>] for one language: refuse typos."""
    import difflib
    def rules(table, where):
        for k, v in table.items():
            if k not in EXPECT_KEYS or isinstance(v, dict):
                near = difflib.get_close_matches(k, EXPECT_KEYS, n=1)
                raise Fail(f"[{where}] in {name} has an unknown setting '{k}'" + (f"; did you mean '{near[0]}'?" if near else f". Known settings: {', '.join(EXPECT_KEYS)}"))
            if not (isinstance(v, list) and v and all(isinstance(t, str) and t.strip() for t in v)):
                raise Fail(f"[{where}] {k} in {name} should be a list of texts, e.g. {k} = [\"Senior iOS Engineer\"]")
    for shot, table in expect.items():
        if not isinstance(table, dict):
            raise Fail(f"[expect] in {name}: '{shot}' should be a table named after a screenshot, e.g. [expect.{shot}] with any = [\"text\"]")
        rules({k: v for k, v in table.items() if not isinstance(v, dict) or k in EXPECT_KEYS}, f"expect.{shot}")
        for locale, sub in table.items():
            if isinstance(sub, dict) and locale not in EXPECT_KEYS: rules(sub, f"expect.{shot}.{locale}")

def read_doc(config_path):
    """The parsed config file; a missing file or bad TOML is a Fail that says how to fix it."""
    cfg_path = Path(config_path).expanduser().resolve()
    if not cfg_path.is_file():
        raise Fail(f"no config at {cfg_path}. Create one with: shotfleet init <App.app | app.apk>")
    try: doc = tomllib.loads(cfg_path.read_text())
    except tomllib.TOMLDecodeError as e: raise Fail(f"{cfg_path.name} isn't valid TOML: {e}")
    check_tables(doc, cfg_path.name)
    return cfg_path, doc

def read_expect(config_path):
    """The [expect.*] tables of a config, for `check --content` (no build, Maestro or licence needed)."""
    cfg_path, doc = read_doc(config_path)
    if not doc.get("expect"):
        raise Fail(f"{cfg_path.name} has no [expect.<screenshot>] table. Add one, e.g. [expect.01_home] with any = [\"text that must be on screen\"]")
    return doc["expect"]

def platforms_in(config_path):
    """The platform sections ([ios], [android]) a config file has, in run order."""
    cfg_path, doc = read_doc(config_path)
    found = [k for k in ("ios", "android") if k in doc]
    if not found: raise Fail(f"{cfg_path.name} needs an [ios] or an [android] section")
    return found

def check_section(cfg, platform, name):
    """Refuse an unknown key or a wrong type in [ios] / [android] (no files are read; load_config adds the checks that need the build)."""
    known = {**KEYS["common"], **KEYS[platform]}
    for key, value in cfg.items():
        if key not in known:
            import difflib
            near = difflib.get_close_matches(key, known, n=1)
            raise Fail(f"[{platform}] in {name} has an unknown setting '{key}'" +
                       (f"; did you mean '{near[0]}'?" if near else f". Known settings: {', '.join(sorted(known))}"))
        want = known[key]
        if not isinstance(value, want) or (want is int and isinstance(value, bool)):  # bool is an int in Python
            names = want.__name__ if isinstance(want, type) else " or ".join(t.__name__ for t in want)
            names = names.replace("str", "string").replace("int", "whole number").replace("bool", "true/false")
            raise Fail(f"[{platform}] {key} in {name} should be a {names}, not {value!r}")
    for key in ("parallel", "timeout_s", "stall_s"):  # the command line refuses --parallel 0; the config must too ("booting 0 simulators")
        if key in cfg and cfg[key] < 1: raise Fail(f"[{platform}] {key} in {name} should be 1 or more, not {cfg[key]}")
    for key in ("locales", "device_types", "devices", "strings"):
        if isinstance(cfg.get(key), list) and not all(isinstance(v, str) for v in cfg[key]):
            raise Fail(f"[{platform}] {key} in {name} should be a list of strings, e.g. {key} = [\"de\", \"ja\"]")
    if cfg.get("locales") == []:  # an empty --locales is refused; an empty list in the config would silently capture every language
        raise Fail(f"[{platform}] locales in {name} is empty. Remove the line to capture every language the app ships, or list some: locales = [\"de\", \"ja\"]")
    for key in ("shell", "simctl"):  # commands for the device after boot: every one a string (simctl ones also splittable)
        if not all(isinstance(c, str) for c in cfg.get(key, [])):
            raise Fail(f"[{platform}] {key} in {name} should be a list of commands (strings), e.g. {key} = [{EXAMPLE_SETUP[key]}]")
        for c in cfg.get(key, []):
            try: shlex.split(c)
            except ValueError as e: raise Fail(f"[{platform}] {key} in {name}: can't read '{c}': {e}")

def load_config(config_path, platform=None):
    """(platform, cfg, path resolver) for one section, with every mistake reported as a Fail that says how to fix it."""
    cfg_path, doc = read_doc(config_path)
    platforms = [k for k in ("ios", "android") if k in doc]
    if not platforms:
        raise Fail(f"{cfg_path.name} needs an [ios] or an [android] section")
    platform = platform or platforms[0]
    if platform not in doc: raise Fail(f"{cfg_path.name} has no [{platform}] section")
    cfg = doc[platform]
    check_section(cfg, platform, cfg_path.name)
    cfg["_config"], cfg["_hooks"], cfg["_overrides"] = str(cfg_path), doc.get("hooks", {}), doc.get("overrides", {})
    cfg["_inputs"], cfg["_expect"] = doc.get("inputs", {}), doc.get("expect", {})
    cfg.setdefault("flow", "flow.yaml")
    cfg.setdefault("out", "out" if len(platforms) == 1 else f"out-{platform}")  # two platforms must not share a folder
    missing = [k for k in REQUIRED[platform] if not cfg.get(k)]
    if missing:
        raise Fail(f"[{platform}] in {cfg_path.name} is missing: {', '.join(missing)}")
    path = lambda p: cfg_path.parent / Path(p).expanduser()  # absolute/~ paths win, others are relative to the config
    flow = path(cfg["flow"])
    if not flow.is_file():
        raise Fail(f"flow file not found: {flow}. `shotfleet init` writes a starter flow")
    if platform == "ios":
        app = path(cfg["app"])
        if not (app / "Info.plist").is_file():
            if app.exists() and app.suffix != ".app": raise Fail(f"{app} isn't a simulator app: {not_a_build(app, 'ios')}")
            raise Fail(f"no simulator app at {app}. Build it for the simulator (Debug-iphonesimulator) and point 'app' at the .app")
        real = plist_value(app / "Info.plist", "CFBundleIdentifier")
        if cfg.get("bundle_id") and real and real != cfg["bundle_id"]:
            raise Fail(f"bundle_id is {cfg['bundle_id']} but {app.name} is {real}")
        cfg["bundle_id"] = cfg.get("bundle_id") or real
        if not cfg["bundle_id"]: raise Fail(f"can't read the bundle id of {app.name}; set bundle_id in the config")
        if device_build(app):
            raise Fail(device_build_message(app))
        cfg["app"] = str(app)
    else:
        apk = path(cfg["apk"])
        if not apk.is_file() or apk.suffix.lower() != ".apk":
            raise Fail(f"{apk} isn't an APK: {not_a_build(apk, 'android')}" if apk.exists() else f"no APK at {apk}")
        m = re.search(r"package: name='([^']+)'", sh([aapt2(), "dump", "badging", str(apk)]).stdout)
        if m and cfg.get("package") and m.group(1) != cfg["package"]:
            raise Fail(f"package is {cfg['package']} but the APK is {m.group(1)}")
        cfg["package"] = cfg.get("package") or (m and m.group(1))
        if not cfg["package"]: raise Fail(f"can't read the package name of {apk.name}; set package in the config")
        cfg["apk"] = str(apk)
    if not maestro_cmd():
        raise Fail("Maestro isn't installed. Run shotfleet doctor --fix, or install it with: curl -Ls https://get.maestro.mobile.dev | bash")
    return platform, cfg, path
# lproj code -> App Store Connect / fastlane locale
# Store listing codes, exactly as fastlane deliver/supply folder names (sources: marketing/store-locales.md, 2026-10-01)
APP_STORE = ("ar-SA bn-BD ca cs da de-DE el en-AU en-CA en-GB en-US es-ES es-MX fi fr-CA fr-FR gu-IN he hi hr hu id it "
             "ja kn-IN ko ml-IN mr-IN ms nl-NL no or-IN pa-IN pl pt-BR pt-PT ro ru sk sl-SI sv ta-IN te-IN th tr uk "
             "ur-PK vi zh-Hans zh-Hant").split()
PLAY = ("af sq am ar hy-AM az-AZ bn-BD eu-ES be bg my-MM ca zh-HK zh-CN zh-TW hr cs-CZ da-DK nl-NL en-AU en-CA en-US "
        "en-GB en-IN en-SG en-ZA et fil fi-FI fr-CA fr-FR gl-ES ka-GE de-DE el-GR gu iw-IL hi-IN hu-HU is-IS id it-IT "
        "ja-JP kn-IN kk km-KH ko-KR ky-KG lo-LA lv lt mk-MK ms-MY ms ml-IN mr-IN mn-MN ne-NP no-NO fa fa-AE fa-AF fa-IR "
        "pl-PL pt-BR pt-PT pa ro rm ru-RU sr si-LK sk sl es-419 es-ES es-US sw sv-SE ta-IN te-IN th tr-TR uk ur vi zu").split()
# When a language has several listings and the app's locale names no region, its screenshots go to this one
PRIMARY = {"en": "en-US", "es": "es-ES", "fr": "fr-FR", "pt": "pt-BR", "zh": "zh-Hans", "ms": "ms", "fa": "fa"}
# App locale spellings -> one canonical form: Android's legacy codes, Chinese by script, Norwegian, old lproj names
LANG_CANON = {"in": "id", "iw": "he", "ji": "yi", "tl": "fil", "nb": "no", "nn": "no"}
CANON = {"zh": "zh-Hans", "zh-CN": "zh-Hans",
         "zh-SG": "zh-Hans", "zh-TW": "zh-Hant", "zh-HK": "zh-Hant-HK", "zh-MO": "zh-Hant-HK", "es-MX": "es-419",
         "English": "en", "French": "fr", "German": "de", "Japanese": "ja", "Spanish": "es", "Italian": "it", "Dutch": "nl"}

def canon(code):
    lang, _, rest = code.replace("_", "-").partition("-")
    code = LANG_CANON.get(lang, lang) + ("-" + rest if rest else "")
    return CANON.get(code, code)

def store_code(app_locale, store):
    """The listing an app locale's screenshots belong to in `store` (APP_STORE or PLAY), or None if that store
    has no listing in that language. E.g. App Store: de -> de-DE, nb -> no, zh-Hant-HK -> zh-Hant; Play: iw -> iw-IL."""
    c = canon(app_locale)
    by_canon = {}
    for code in store:
        by_canon.setdefault(canon(code), code)
    if c in by_canon: return by_canon[c]
    lang, *rest = c.split("-")
    same = [code for code in store if canon(code).split("-")[0] == lang]
    if lang == "zh":  # by script; Hong Kong falls back to Traditional
        same = [code for code in same if canon(code).startswith("zh-Hant" if "Hant" in c else "zh-Hans")]
    if lang == "es" and rest and rest[0] != "ES":  # any Latin American Spanish -> es-419 / es-MX
        same = [code for code in same if code in ("es-419", "es-MX")] or same
    if rest:
        regional = [code for code in same if code.split("-")[-1] == rest[-1]]
        if regional: return regional[0]
    if len(same) > 1:
        primary = [code for code in same if code == PRIMARY.get(lang) or canon(code) == canon(PRIMARY.get(lang, ""))]
        plain = [code for code in same if "-" not in canon(code)] or [code for code in same if code.split("-")[-1].lower() == lang]
        return (primary or plain or same)[0]
    return same[0] if same else None

# lproj code -> language NLLanguageRecognizer reports (differs only for these)
EXPECTED_LANG = {"nb": "nb", "zh-Hans": "zh-Hans", "zh-Hant": "zh-Hant"}
SELECTOR_KEYS = ("tapOn", "doubleTapOn", "longPressOn", "assertVisible", "assertNotVisible",
                 "scrollUntilVisible", "text", "copyTextFrom", "visible", "notVisible",
                 "below", "above", "leftOf", "rightOf", "childOf", "containsChild")  # relative anchors are text too

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def aapt2():
    """Newest aapt2 in the Android SDK; Fail with the fix if there is none."""
    found = sorted((SDK / "build-tools").glob("*/aapt2"))
    if not found and shutil.which("aapt2"): return shutil.which("aapt2")  # Linux: the distribution's aapt2 package
    if not found:
        raise Fail(f"aapt2 not found under {SDK}/build-tools. Install Build-Tools in Android Studio's SDK Manager (or set ANDROID_HOME)")
    return str(found[-1])

# ---------- strings ----------

def plist_value(plist, key):
    """A top-level Info.plist value, or "" (PlistBuddy prints its errors on stdout). Without PlistBuddy (Linux) the
    value is read in Python and printed the way PlistBuddy would: arrays as "Array {", one item per line, "}"."""
    if not Path(plist).is_file(): return ""
    if not shutil.which("/usr/libexec/PlistBuddy"):
        v = read_plist(plist).get(key)
        if v is None: return ""
        if isinstance(v, list): return "Array {\n" + "".join(f"    {x}\n" for x in v) + "}"
        return str(v).lower() if isinstance(v, bool) else str(v)
    r = sh(["/usr/libexec/PlistBuddy", "-c", f"Print {key}", str(plist)])
    return r.stdout.strip() if r.returncode == 0 else ""

_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", "a": "\a", "b": "\b", "f": "\f", "v": "\v", '"': '"', "'": "'", "\\": "\\"}

def parse_strings_text(text):
    """A .strings file (`"key" = "value";` with /* */ and // comments, \\n \\" \\UXXXX escapes) as {key: value}.
    The old-style plist plutil reads; Linux has no plutil. Raises ValueError on anything else."""
    pos, n, out = 0, len(text), {}
    def skip():
        nonlocal pos
        while pos < n:
            if text[pos].isspace() or text[pos] == "﻿": pos += 1
            elif text.startswith("/*", pos):
                end = text.find("*/", pos + 2)
                if end < 0: raise ValueError("unterminated comment")
                pos = end + 2
            elif text.startswith("//", pos):
                end = text.find("\n", pos)
                pos = n if end < 0 else end
            else: break
    def token():
        nonlocal pos
        skip()
        if pos >= n: raise ValueError("unexpected end")
        if text[pos] in "\"'":
            q, pos, buf = text[pos], pos + 1, []
            while pos < n and text[pos] != q:
                c = text[pos]
                if c == "\\" and pos + 1 < n:
                    e = text[pos + 1]
                    if e in "uU" and re.match(r"[0-9a-fA-F]{4}", text[pos + 2:pos + 6]): buf.append(chr(int(text[pos + 2:pos + 6], 16))); pos += 6; continue
                    if e in "01234567" and re.match(r"[0-7]{3}", text[pos + 1:pos + 4]): buf.append(chr(int(text[pos + 1:pos + 4], 8))); pos += 4; continue
                    buf.append(_ESCAPES.get(e, e)); pos += 2; continue
                buf.append(c); pos += 1
            if pos >= n: raise ValueError("unterminated string")
            pos += 1
            return "".join(buf)
        m = re.compile(r"[\w.$/:+-]+").match(text, pos)  # unquoted key or value
        if not m: raise ValueError(f"unexpected {text[pos]!r}")
        pos = m.end()
        return m.group()
    skip()
    if pos < n and text[pos] == "{": pos += 1  # the same table wrapped in { } is a plist dictionary
    while True:
        skip()
        if pos >= n or text[pos] == "}": return out
        key = token(); skip()
        if pos < n and text[pos] == ";": pos += 1; out[key] = key; continue  # `key;` means key = key
        if pos >= n or text[pos] != "=": raise ValueError(f"expected = after {key!r}")
        pos += 1
        out[key] = token(); skip()
        if pos >= n or text[pos] != ";": raise ValueError(f"expected ; after the value of {key!r}")
        pos += 1

def plist_to_json(path):
    """A property list as plain data (dict/list/str), or None when unreadable. plutil where macOS has it (it also reads
    binary and old-style plists); otherwise XML and binary plists through plistlib and .strings text in Python."""
    path = Path(path)
    if shutil.which("plutil"):
        r = sh(["plutil", "-convert", "json", "-o", "-", str(path)])
        return json.loads(r.stdout) if r.returncode == 0 else None
    try: raw = path.read_bytes()
    except OSError: return None
    try: return json.loads(json.dumps(plistlib.loads(raw), default=lambda o: o.hex() if isinstance(o, bytes) else str(o)))
    except Exception: pass
    for enc in (("utf-16",) if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else ("utf-8-sig", "utf-16-le" if b"\0" in raw[:20] else "latin-1")):
        try: return parse_strings_text(raw.decode(enc))
        except (UnicodeDecodeError, ValueError): continue
    return None

def load_strings(res_dir):
    """{lproj: {key: value}} from every *.strings table in the app: its own *.lproj folders, plus those inside
    frameworks, Swift package bundles and an embedded Watch app (keys there are prefixed with their bundle path),
    plus Compose Multiplatform resources (*.cvr)."""
    res_dir, out = Path(res_dir), {}
    for lproj in sorted(res_dir.rglob("*.lproj")):
        if lproj.stem == "Base": continue  # Base.lproj is layout/fallback storage, not a language
        where = lproj.parent.relative_to(res_dir).as_posix()
        for f in sorted(lproj.glob("*.stringsdict")):
            data = plist_to_json(f)
            if data is not None:
                table = stringsdict_forms(data)
                if where != ".": table = {f"{where}/{f.stem}:{k}": v for k, v in table.items()}
                out.setdefault(canon_lproj(lproj.stem), {}).update(table)
        for f in sorted(lproj.glob("*.strings")):
            table = plist_to_json(f)
            if isinstance(table, dict):
                if where != ".": table = {f"{where}/{f.stem}:{k}": v for k, v in table.items()}
                out.setdefault(canon_lproj(lproj.stem), {}).update(table)
    for f in sorted(res_dir.rglob("*.cvr")):
        add_cvr(out, f.relative_to(res_dir).as_posix(), f.read_text(errors="replace"), "en")
    out = {lp: t for lp, t in out.items() if t}
    # String Catalogs keyed by their English text ("Next" = "Weiter") ship no English table for those keys:
    # the key is the development-language string
    dev = plist_value(res_dir / "Info.plist", "CFBundleDevelopmentRegion") or "en"
    dev = canon_lproj(dev) if dev in out or dev[:1].isupper() else dev
    keys = {k for lp, t in out.items() if lp != dev for k in t}
    if keys:
        base = out.setdefault(dev, {})
        for k in keys - base.keys():
            if "#" in k: continue  # plural forms (few, many) English doesn't have
            base[k] = k.split(":", 1)[1] if "/" in k.split(":", 1)[0] and ":" in k else k
    return out

def stringsdict_forms(d):
    """{key#form: text} for every plural/device/width form in a .stringsdict, e.g. items#one = "1 item".
    A form's text replaces its %#@var@ in the format; other variables take their 'other' form."""
    out = {}
    for key, entry in d.items():
        if not isinstance(entry, dict): continue
        if "NSStringDeviceSpecificRuleType" in entry or "NSStringVariableWidthRuleType" in entry:
            rules = entry.get("NSStringDeviceSpecificRuleType") or entry.get("NSStringVariableWidthRuleType")
            for form, text in rules.items():
                if isinstance(text, str): out[f"{key}#{form}"] = text
            continue
        fmt = entry.get("NSStringLocalizedFormatKey", "")
        variables = {v: forms for v, forms in entry.items() if isinstance(forms, dict)}
        def fill(text, skip):
            for v, forms in variables.items():
                if v != skip: text = text.replace(f"%#@{v}@", forms.get("other", ""))
            return text
        for v, forms in variables.items():
            for form, text in forms.items():
                if not form.startswith("NSString") and isinstance(text, str):
                    tag = form if len(variables) == 1 else f"{v}.{form}"
                    out[f"{key}#{tag}"] = fill(fmt.replace(f"%#@{v}@", text), v)
    return out

def canon_lproj(name):
    """Old lproj names (English.lproj) and underscores (en_GB.lproj) -> the code iOS uses for AppleLanguages."""
    name = name.replace("_", "-")
    return CANON.get(name, name) if name[:1].isupper() else name

CVR_DIR = re.compile(r"composeResources/[^/]+/values(?:-([^/]+))?/[^/]+\.cvr$")

def add_cvr(out, path, text, base):
    """Compose Multiplatform resources: lines of 'string|key|base64(value)' in composeResources/<pkg>/values-<q>/*.cvr."""
    m = CVR_DIR.search(path)
    loc = m and (base if m.group(1) is None else android_locale(m.group(1)))
    if not loc: return
    for line in text.splitlines():
        kind, key, value = (line.split("|", 2) + ["", ""])[:3]
        if kind == "string":
            out.setdefault(loc, {})[f"cmp:{key}"] = unescape_android(base64.b64decode(value).decode("utf-8", "replace"))
        elif kind == "plurals":  # ponytail: format inferred from compose-resources' writer, not seen in a real app yet
            for item in value.split(","):
                form, _, b64 = item.partition(":")
                if b64: out.setdefault(loc, {})[f"cmp:{key}#{form}"] = unescape_android(base64.b64decode(b64).decode("utf-8", "replace"))

LOCALE_QUALIFIER = re.compile(r"^(?:([a-z]{2,3})(?:-r([A-Z]{2}))?|b\+([a-z]{2,3})((?:\+[A-Za-z0-9]+)*))$")

def android_locale(q):
    """aapt2 config qualifier -> BCP-47 tag ('de', 'pt-rBR' -> 'pt-BR', 'b+zh+Hans' -> 'zh-Hans'); None if not a pure locale."""
    m = LOCALE_QUALIFIER.match(q)
    if not m or q in ("car", "en-rXA", "ar-rXB", "en-rXC"): return None  # 'car' is a UI mode; X? are pseudolocales
    if m.group(3): return m.group(3) + m.group(4).replace("+", "-")
    return m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")

# ---------- strings from source files (Flutter, React Native, .NET, Unity, translation platforms) ----------

KNOWN_LANGS = {c.split("-")[0].lower() for c in APP_STORE + PLAY} | {"en"}

def locale_from_path(path, codes=None):
    """Language of a translation file from how ecosystems name them: app_de.arb, de.json, Resources.de.resx,
    messages_pt_BR.properties, locales/de/translation.json, values-de/strings.xml, de.lproj/... None if unknown."""
    path = Path(path)
    ok = lambda c: re.fullmatch(r"[a-z]{2,3}(?:[-_](?:[A-Z]{2}|[A-Z][a-z]{3}|\d{3}))*", c or "")
    stem = path.name.split(".")[0] if path.suffix != ".lproj" else path.stem
    parts = path.name.split(".")
    if len(parts) >= 3 and ok(parts[-2]): return parts[-2].replace("_", "-")         # Resources.de.resx, en.lproj
    lang = lambda c: c.split("-")[0].split("_")[0].lower() in KNOWN_LANGS
    if ok(path.parent.name) and lang(path.parent.name) and not lang(stem):           # locales/en/app.json: a namespace file
        return path.parent.name.replace("_", "-")
    if ok(stem): return stem.replace("_", "-")                                       # de.json, de.po
    if m := re.search(r"[_-]([a-z]{2,3}(?:[-_](?:[A-Z]{2}|[A-Z][a-z]{3}))?)$", stem):  # app_de.arb, messages_pt_BR
        return m.group(1).replace("_", "-")
    for d in [path.parent, *path.parent.parents][:3]:
        if d.name.startswith("values"):
            return android_locale(d.name[7:]) if d.name != "values" else "base"
        if d.suffix == ".lproj": return d.stem
        if ok(d.name) and lang(d.name): return d.name.replace("_", "-")  # app/i18n/index.ts is not "app" (a folder, not a language)
    return None

def icu_forms(key, text):
    """{key: text} or, for ICU plural/select ('{n, plural, one{# item} other{# items}}'), one entry per form,
    with '#' standing for the number. ponytail: the first plural/select block only; nested ones stay as text."""
    m = re.search(r"\{\s*(\w+)\s*,\s*(plural|select|selectordinal)\s*,", text)
    if not m: return {key: text}
    depth, i = 1, m.end()
    while i < len(text) and depth:
        depth += {"{": 1, "}": -1}.get(text[i], 0); i += 1
    body, head, tail = text[m.end():i - 1], text[:m.start()], text[i:]
    out = {}
    for f in re.finditer(r"\s*(=?\w+)\s*\{", body):
        if f.start() and body[f.start() - 1] not in " }\n\t": continue
        d, j = 1, f.end()
        while j < len(body) and d:
            d += {"{": 1, "}": -1}.get(body[j], 0); j += 1
        form_text = body[f.end():j - 1].replace("#", "{%s}" % m.group(1))
        out[f"{key}#{f.group(1)}"] = head + form_text + tail
    return out or {key: text}

def icu_forms_all(flat):
    """(key, text) pairs of a flattened i18next-style table: key_one/key_other become key#one/key#other, ICU plurals one entry per form."""
    for k, v in flat.items():
        k = re.sub(r"_(zero|one|two|few|many|other)$", r"#\1", k)
        yield from icu_forms(k, v).items()

def flatten(d, prefix=""):
    """Nested JSON (i18next, Lokalise) -> {'a.b.c': text}."""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict): out.update(flatten(v, f"{prefix}{k}."))
        elif isinstance(v, str): out[prefix + k] = v
    return out

def strip_js_comments(src):
    """`src` without // and /* */ comments; string and template literals are left alone."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in "\"'`":
            j = i + 1
            while j < n and src[j] != c: j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1]); i = j + 1
        elif src.startswith("//", i):
            j = src.find("\n", i); i = n if j < 0 else j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2); i = n if j < 0 else j + 2
        else: out.append(c); i += 1
    return "".join(out)

JS_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}

def parse_js_translations(src):
    """({key: text or nested dict}, skipped) for the object literal that holds a translation file's texts, read as data and
    never run: `export default {..}`, `const en = {..}`, `const de: Translations = {..}`, `module.exports = {..}`. Strings,
    template literals without ${}, 'a' + 'b', nested objects and arrays of strings are read; anything that is code (calls,
    variables, functions, spreads) is skipped and counted. Raises ValueError when no object literal is found."""
    text = strip_js_comments(src)
    m = re.search(r"(?:export\s+default\s*(?:\w+\s*\(\s*)?|module\.exports\s*=\s*|exports\.\w+\s*=\s*|\b(?:const|let|var)\s+[\w$]+\s*(?::[^=;{]+?)?=\s*)\(?\s*(?=\{)", text)
    if not m: raise ValueError("no object literal with the translations found (export default { ... } or const en = { ... })")
    pos, n, skipped = m.end(), len(text), []
    def ws():
        nonlocal pos
        while pos < n and text[pos].isspace(): pos += 1
    def string():
        nonlocal pos
        q = text[pos]; pos += 1; buf = []; dynamic = False
        while pos < n and text[pos] != q:
            c = text[pos]
            if c == "\\" and pos + 1 < n:
                e = text[pos + 1]
                if e == "u" and re.match(r"[0-9a-fA-F]{4}", text[pos + 2:pos + 6]): buf.append(chr(int(text[pos + 2:pos + 6], 16))); pos += 6; continue
                if e == "u" and text[pos + 2:pos + 3] == "{":
                    end = text.find("}", pos); buf.append(chr(int(text[pos + 3:end], 16))); pos = end + 1; continue
                if e == "x" and re.match(r"[0-9a-fA-F]{2}", text[pos + 2:pos + 4]): buf.append(chr(int(text[pos + 2:pos + 4], 16))); pos += 4; continue
                if e == "\n": pos += 2; continue
                buf.append(JS_ESCAPES.get(e, e)); pos += 2; continue
            if q == "`" and c == "$" and text[pos + 1:pos + 2] == "{": dynamic = True
            buf.append(c); pos += 1
        pos += 1
        return None if dynamic else "".join(buf)
    def skip_expr():
        nonlocal pos
        depth = 0
        while pos < n:
            c = text[pos]
            if c in "\"'`": string(); continue
            if c in "([{": depth += 1
            elif c in ")]}":
                if depth == 0: return
                depth -= 1
            elif c == "," and depth == 0: return
            pos += 1
    def value(name):
        nonlocal pos
        ws()
        if pos >= n: raise ValueError("the file ends inside the translations")
        c = text[pos]
        if c in "\"'`":
            v = string(); ws()
            while v is not None and text[pos:pos + 1] == "+":  # "a" + "b"
                pos += 1; ws()
                if pos < n and text[pos] in "\"'`": w = string(); v = None if w is None else v + w; ws()
                else: v = None; skip_expr()
            if v is None or text[pos:pos + 1] not in (",", "}", "]", ""): 
                if text[pos:pos + 1] not in (",", "}", "]", ""): skip_expr()
                skipped.append(name); return None
            return v
        if c == "{": return obj()
        if c == "[":
            pos += 1; items = []
            while True:
                ws()
                if pos >= n: raise ValueError("missing ] in the translations")
                if text[pos] == "]": pos += 1; return {str(i): v for i, v in enumerate(items) if v is not None}
                items.append(value(f"{name}[{len(items)}]")); ws()
                if text[pos:pos + 1] == ",": pos += 1
        skip_expr(); skipped.append(name); return None  # a call, a variable, a function, a number...
    def obj(prefix=""):
        nonlocal pos
        pos += 1; out = {}
        while True:
            ws()
            if pos >= n: raise ValueError("missing } in the translations")
            if text[pos] == "}": pos += 1; return out
            if text.startswith("...", pos): skip_expr(); skipped.append("..."); pos += text[pos:pos + 1] == ","; continue
            if text[pos] in "\"'": key = string()
            elif text[pos] == "[": skip_expr(); skipped.append("[computed]"); pos += text[pos:pos + 1] == ","; continue
            else:
                km = re.compile(r"[\w$]+").match(text, pos)
                if not km: raise ValueError(f"unexpected {text[pos]!r} in the translations")
                key, pos = km.group(), km.end()
            ws()
            if text[pos:pos + 1] != ":": skip_expr(); skipped.append(key); pos += text[pos:pos + 1] == ","; continue  # shorthand or method
            pos += 1
            v = value(key); ws()
            if v is not None and key is not None: out[key] = v
            if text[pos:pos + 1] == ",": pos += 1
    return obj(), skipped

def read_translation_file(f, base):
    """{locale: {key: text}} from one source file, by format."""
    f, ext = Path(f), Path(f).suffix.lower()
    lp = locale_from_path(f)
    lp = base if lp in (None, "base") else lp
    if ext == ".arb":  # Flutter: {"@@locale": "de", "next": "Weiter", "@next": {...}}
        d = json.loads(f.read_text())
        lp = d.get("@@locale", lp).replace("_", "-")
        out = {}
        for k, v in d.items():
            if not k.startswith("@") and isinstance(v, str): out.update(icu_forms(k, v))
        return {lp: out}
    if ext == ".json":  # i18next / react-intl / Lokalise: nested keys, key_one/key_other plurals
        return {lp: dict(icu_forms_all(flatten(json.loads(f.read_text()))))}
    if ext in (".ts", ".tsx", ".js", ".mjs", ".cjs"):  # Ignite, i18n-js, vue-i18n: translations written as an object in code
        try: tree, skipped = parse_js_translations(f.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            raise Fail(f"can't read {f.name} as a translation file: {e}")
        if skipped: print(f"note: {f.name}: {len(skipped)} entr{'y is' if len(skipped) == 1 else 'ies are'} code, not text, and skipped "
                          f"({', '.join(dict.fromkeys(skipped))[:80]})", file=sys.stderr)
        langs = {k: v for k, v in tree.items() if isinstance(v, dict) and locale_from_path(Path(k + ".json")) is not None}
        if tree and len(langs) == len(tree):  # { en: {...}, de: {...} }: one file, every language
            return {k: dict(icu_forms_all(flatten(v))) for k, v in langs.items()}
        if locale_from_path(f) in (None, "base"): return {}  # index.ts, i18n.ts and other code next to the language files
        return {lp: dict(icu_forms_all(flatten(tree)))}
    if ext == ".xcstrings":  # String Catalog source: every language in one file
        d, out = json.loads(f.read_text()), {}
        src = d.get("sourceLanguage", base)
        for key, entry in d.get("strings", {}).items():
            locs = entry.get("localizations", {})
            if src not in locs: out.setdefault(src, {})[key] = key  # source text is the key
            for loc, l in locs.items():
                if "stringUnit" in l: out.setdefault(loc, {})[key] = l["stringUnit"].get("value", "")
                for kind in ("plural", "device"):
                    for form, v in l.get("variations", {}).get(kind, {}).items():
                        if "stringUnit" in v: out.setdefault(loc, {})[f"{key}#{form}"] = v["stringUnit"].get("value", "")
        return out
    if ext in (".strings", ".stringsdict"):
        d = plist_to_json(f)
        if d is None: return {}
        return {lp: stringsdict_forms(d) if ext == ".stringsdict" else d}
    if ext == ".xml":  # Android strings.xml / Compose Multiplatform composeResources
        root, out = ET.parse(f).getroot(), {}
        def text(e):  # Android: "..." around the whole value only preserves whitespace
            t = "".join(e.itertext()).strip()
            return unescape_android(t[1:-1] if len(t) >= 2 and t[0] == t[-1] == '"' else t)
        for e in root:
            if e.tag == "string" and e.get("translatable") != "false": out[e.get("name")] = text(e)
            elif e.tag == "plurals":
                for item in e.findall("item"): out[f"{e.get('name')}#{item.get('quantity')}"] = text(item)
            elif e.tag == "string-array":  # spinner and picker entries: name[0], name[1]...
                for n, item in enumerate(e.findall("item")): out[f"{e.get('name')}[{n}]"] = text(item)
        return {lp: out}
    if ext in (".xlf", ".xliff"):  # XLIFF 1.2/2.0 exports: source and target languages in one file
        root = ET.parse(f).getroot()
        ns = lambda tag: [e for e in root.iter() if e.tag.split("}")[-1] == tag]
        out = {}
        for fl in ns("file") or [root]:
            src = (fl.get("source-language") or root.get("srcLang") or base)
            tgt = (fl.get("target-language") or root.get("trgLang") or lp)
            for u in [e for e in fl.iter() if e.tag.split("}")[-1] in ("trans-unit", "unit")]:
                key = u.get("id") or u.get("resname")
                get = lambda tag: next(("".join(e.itertext()) for e in u.iter() if e.tag.split("}")[-1] == tag), None)
                if (v := get("source")) is not None: out.setdefault(src, {})[key] = v
                if (v := get("target")) is not None and tgt: out.setdefault(tgt, {})[key] = v
        return out
    if ext == ".resx":  # .NET / MAUI: Resources.resx (base), Resources.de.resx
        root = ET.parse(f).getroot()
        return {lp: {d.get("name"): d.findtext("value", "") for d in root.findall("data") if d.get("type") is None}}
    if ext == ".po":  # gettext: msgid is the source text
        entries = []
        for block in re.split(r"\n\s*\n", f.read_text(errors="replace")):
            fields, cur = {}, None
            for line in block.splitlines():
                line = line.strip()
                if m := re.match(r'(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?)\s+(".*")$', line):
                    cur = m.group(1); fields[cur] = json.loads(m.group(2))
                elif line.startswith('"') and cur: fields[cur] += json.loads(line)
            if "msgid" in fields: entries.append(fields)
        if locale_from_path(f) is None:  # no language in the path: use the file's own "Language:" header
            head = next((e.get("msgstr", "") for e in entries if e["msgid"] == ""), "")
            if m := re.search(r"^Language:\s*([A-Za-z]{2,3}(?:[_-][A-Za-z0-9]+)*)", head, re.M): lp = m.group(1).replace("_", "-")
        out, src = {}, {}
        for e in entries:
            key = f"{e['msgctxt']}|{e['msgid']}" if e.get("msgctxt") else e["msgid"]
            if not e["msgid"]: continue
            if "msgid_plural" in e:  # every plural form is an alternative: no per-language plural rules needed
                for k, v in e.items():
                    if k.startswith("msgstr[") and v: out[f"{key}#{k[7:-1]}"] = v
                src[f"{key}#0"], src[f"{key}#1"] = e["msgid"], e["msgid_plural"]
            elif e.get("msgstr"): out[key] = e["msgstr"]; src[key] = e["msgid"]
        return {lp: out, base: src} if lp != base else {base: {**src, **out}}
    if ext == ".properties":  # Java/Kotlin ResourceBundle
        out = {}
        for line in f.read_text(errors="replace").splitlines():
            if line.strip() and not line.lstrip().startswith(("#", "!")) and ("=" in line or ":" in line):
                k, v = (re.split(r"\s*[=:]\s*", line.strip(), maxsplit=1) + [""])[:2]
                out[k] = v.encode().decode("unicode_escape") if "\\u" in v else v
        return {lp: out}
    if ext == ".csv":  # Unity Localization / spreadsheet exports: Key,en,de,...
        rows = list(csv.reader(f.read_text(errors="replace").splitlines()))
        if not rows: return {}
        head, out = rows[0], {}
        langs = [(i, h.split("(")[-1].rstrip(")").strip() if "(" in h else h.strip()) for i, h in enumerate(head[1:], 1)]
        for r in rows[1:]:
            for i, l in langs:
                if i < len(r) and r[i] and re.fullmatch(r"[a-z]{2,3}(?:[-_][A-Za-z0-9]+)*", l):
                    out.setdefault(l.replace("_", "-"), {})[r[0]] = r[i]
        return out
    raise Fail(f"don't know how to read {f.name}: supported are .arb .json .xcstrings .strings .stringsdict .xml "
               ".xlf .xliff .resx .po .properties .csv")

def config_strings(cfg, path):
    """The config's `strings`: a folder of .lproj, or glob(s) of source files relative to the config. None if unset."""
    if "strings" not in cfg: return None
    pats = [cfg["strings"]] if isinstance(cfg["strings"], str) else cfg["strings"]
    if len(pats) == 1 and path(pats[0]).is_dir() and any(path(pats[0]).glob("*.lproj")):
        return load_strings(path(pats[0]))
    return load_strings_files([str(path(p)) for p in pats], cfg.get("base_locale", "en"))

def run_strings(cfg, path):
    """What run.json keeps of the config's `strings`, as absolute paths: a later `shotfleet check <out>` reads the same translation files
    (without them it can't tell that a language the app only half-translates shows another one)."""
    if "strings" not in cfg: return {}
    pats = [cfg["strings"]] if isinstance(cfg["strings"], str) else cfg["strings"]
    return {"strings": [str(path(p)) for p in pats], "base_locale": cfg.get("base_locale", "en")}

def load_strings_files(patterns, base="en"):
    """{locale: {key: text}} from translation source files matched by glob patterns (relative to cwd or absolute)."""
    files = sorted({f for p in ([patterns] if isinstance(patterns, str) else patterns)
                    for f in glob.glob(os.path.expanduser(p), recursive=True) if Path(f).is_file()})
    if not files: raise Fail(f"no translation files match {patterns}")
    out = {}
    for f in files:
        for lp, t in read_translation_file(f, base).items():
            have = out.setdefault(lp, {})
            for k, v in t.items():  # common.json and settings.json may both define "title": keep both, the later one namespaced
                if k in have and have[k] != v: have[f"{Path(f).stem}:{k}"] = v
                else: have[k] = v
    return {lp: t for lp, t in out.items() if t}

def unescape_android(v):
    """Android resource escapes: \\" \\' \\n \\t \\@ \\? \\uXXXX."""
    v = re.sub(r"(?:\\u[0-9a-fA-F]{4})+", lambda m: m.group(0).encode().decode("unicode_escape")
               .encode("utf-16", "surrogatepass").decode("utf-16"), v)  # emoji arrive as surrogate pairs
    return v.replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n").replace("\\t", "\t") \
            .replace("\\@", "@").replace("\\?", "?")

def load_strings_apk(apk, base="en"):
    """{locale: {name: value}} from the string resources compiled into an APK (default config -> base)."""
    r = sh([aapt2(), "dump", "resources", str(apk)])
    if r.returncode != 0: raise RuntimeError(f"aapt2 dump failed: {r.stderr.strip()}")
    out, name, pending, kind, loc = {}, None, None, None, None
    for line in r.stdout.splitlines():
        if pending is not None:  # a value with newlines continues over the next lines
            pending += "\n" + line.strip()
            if not re.search(r'(?<!\\)"\s*$', line): continue
            line, pending = pending, None
        elif name and (m := re.match(r'\s*\(([^)]*)\) "', line)) and not re.search(r'(?<!\\)"\s*$', line[m.end():]):
            pending = line; continue
        if m := re.match(r"\s*resource 0x[0-9a-f]+ (string|plurals|array)/(\S+)", line):
            name, kind, loc = m.group(2), m.group(1), None; continue
        if name and kind == "array":  # (de) (array) size=2 / ["Klein", "Groß"]
            if m := re.match(r"\s*\(([^)]*)\) \(array\)", line):
                loc = base if m.group(1) == "" else android_locale(m.group(1)); continue
            if loc and re.match(r"\s*\[", line):
                for n, item in enumerate(re.findall(r'"((?:[^"\\]|\\.)*)"', line)): out.setdefault(loc, {})[f"{name}[{n}]"] = unescape_android(item)
                continue
        if name and kind == "plurals":  # (de) (plurals) size=2 / one="..." / other="..."
            if m := re.match(r"\s*\(([^)]*)\) \(plurals\)", line):
                loc = base if m.group(1) == "" else android_locale(m.group(1)); continue
            if loc and (m := re.match(r'\s*(zero|one|two|few|many|other)="(.*)"\s*$', line)):
                out.setdefault(loc, {})[f"{name}#{m.group(1)}"] = unescape_android(m.group(2)); continue
        if name and (m := re.match(r'\s*\(([^)]*)\) "(.*)"\s*$', line, re.S)):
            loc = base if m.group(1) == "" else android_locale(m.group(1))
            if loc:  # skip night/land/v31 and other non-locale variants
                out.setdefault(loc, {})[name] = unescape_android(m.group(2))
        elif not line.startswith("      "):
            name = None
    if not zipfile.is_zipfile(apk): return out
    with zipfile.ZipFile(apk) as z:  # Compose Multiplatform keeps its strings in assets, not resources.arsc
        for n in z.namelist():
            if n.endswith(".cvr"): add_cvr(out, n, z.read(n).decode("utf-8", "replace"), base)
    return out

def partly_translated(strings, base="en", min_coverage=0.5):
    """[(locale, percent)] for languages the app has some of its own strings in, but too few to count as shipped:
    shipped_locales skips them silently, which looks like a bug to the developer who is mid-translation."""
    if base not in strings: return []
    others = [lp for lp in strings if lp != base]
    keep = set(shipped_locales(strings, base, min_coverage))
    counts = {k: sum(k in strings[lp] for lp in others) for k in strings[base]}
    top = max(counts.values(), default=0)
    own = {k for k, c in counts.items() if c < 0.9 * top} if top >= 20 else set(counts)
    if len(own) < 0.1 * len(counts): own = set(counts)
    pct = lambda lp: 100 * sum(k in strings[lp] for k in own) / len(own) if own else 0
    return sorted((lp, round(pct(lp))) for lp in others if lp not in keep and 10 <= pct(lp) < 100 * min_coverage)

def note_partly_translated(strings, base, asked=None):
    """Languages left out because too little is translated; and, for languages the developer asked for by name, a warning up front
    (wger's Japanese is 30%: Flutter shows the base language for every missing string, so those screenshots come out mostly English)."""
    for lp, pct in partly_translated(strings, base):
        if asked is None:
            print(f"note: {lp} is only {pct}% translated in the app, so it is skipped; add locales = [..., \"{lp}\"] to the config to capture it anyway")
        elif lp in asked:
            print(f"warning {lp}: only {pct}% of the app's own strings are translated, so the {lp} screenshots will mostly show {base}; check will say so")

FRAMEWORKS = [  # (name, marker in the build's file names, candidate `strings` globs; the first is the default)
    ("Flutter", r"flutter_assets|libflutter\.so|Flutter\.framework", ["lib/l10n/*.arb", "assets/translations/*.json"]),
    ("React Native", r"main\.jsbundle|index\.android\.bundle|hermes|libreactnativejni|React-Core_privacy|RCTI18nStrings",
     ["src/locales/*/translation.json", "src/translations/*.json", "locales/*.json"]),
    ("Unity", r"UnityFramework|libunity\.so|UnityPlayer", ["Localization/*.csv"]),
    (".NET MAUI", r"Microsoft\.Maui|libmonodroid|libxamarin-app|assemblies\.blob", ["Resources/Strings/*.resx", "Resources/*.resx"]),
]
HINTED = set()  # hints already printed, so a run over many devices says each once

def framework_hint(build, strings_set, root="."):
    """Print (to stderr, once, never blocking) what to add to shotfleet.toml when `build` is Flutter, React Native, MAUI or
    Unity, whose translations are compiled into code shotfleet can't read, and warn about debug builds whose screenshots
    would show a banner or a red box. ponytail: file-name markers only, not confirmed on real builds of every version."""
    b = Path(build)
    names = [p.relative_to(b).as_posix() for p in b.rglob("*")] if b.is_dir() else zipfile.ZipFile(b).namelist() if zipfile.is_zipfile(b) else []
    text = "\n".join(names)
    name, _, globs = next((f for f in FRAMEWORKS if re.search(f[1], text)), (None, None, None))
    if not name: return
    msgs = []
    if not strings_set:
        line = next((g for g in globs if glob.glob(g, root_dir=root)), globs[0])
        msgs.append(f'{name} keeps its translations inside compiled code, which shotfleet cannot read from the build. '
                    f'Add this to shotfleet.toml (point it at your translation files): strings = "{line}"')
    if name == "Flutter" and "kernel_blob.bin" in text:
        msgs.append("this is a Flutter debug build: screenshots show the DEBUG banner unless the app sets "
                    "debugShowCheckedModeBanner: false (iOS simulators only run debug builds; on Android use flutter build apk --release)")
    if name == "React Native" and not re.search(r"main\.jsbundle|index\.android\.bundle", text):
        msgs.append("this React Native build has no JavaScript bundle, so it is a Debug build that loads its code from the Metro "
                    "dev server: screenshots show the red box or fail offline. Build Release (--configuration Release on iOS, --variant release on Android)")
    for m in msgs:
        if m not in HINTED: HINTED.add(m); print("hint: " + m, file=sys.stderr)

def shipped_locales(strings, base="en", min_coverage=0.5):
    """Locales the app itself is translated into.

    Library resources (AndroidX, Material, Play Services) bring their own strings translated into ~80
    locales. Counting raw coverage breaks for apps with few strings of their own: an English-only app
    with 240 strings looks "translated" into 86 languages. So first separate the app's own strings
    (translated into fewer locales than the libraries' near-universal set), then measure coverage of those."""
    if base not in strings: return sorted(strings)
    others = [lp for lp in strings if lp != base]
    counts = {k: sum(k in strings[lp] for lp in others) for k in strings[base]}
    top = max(counts.values(), default=0)
    # libraries come translated into ~80 locales; with fewer locales every key is the app's own
    own = {k for k, c in counts.items() if c < 0.9 * top} if top >= 20 else set(counts)
    if len(own) < 0.1 * len(counts):  # nearly everything is universal: the app itself is translated everywhere
        own = set(counts)
    return sorted([base] + [lp for lp in others
                            if own and sum(k in strings[lp] for k in own) >= min_coverage * len(own)])

def yaml_single_quote(s):
    return "'" + s.replace("'", "''") + "'"

def regex_literal(s):
    # Maestro matches text selectors as a full Java regex; escape metacharacters
    return re.sub(r"([\\.^$|?*+()\[\]{}])", r"\\\1", s)

WRAPPED_RE = re.compile(r"^(\.\*)?(.+?)(\.\*)?$", re.S)

SELECTOR_RE = re.compile(r"^(\s*-?\s*(?:%s):\s*)(.+?)\s*$" % "|".join(SELECTOR_KEYS))

INLINE_RE = re.compile(r"(\b(?:%s)\s*:\s*)(\"[^\"]*\"|'[^']*'|[^,}]+?)(\s*[,}])" % "|".join(SELECTOR_KEYS))

def with_fallback(strings, lp):
    """The strings the app shows in lp, the way iOS and Android resolve them: lp's own, then its parents'
    (zh-Hant-HK -> zh-Hant -> zh, pt-BR -> pt) for keys lp doesn't translate."""
    parts = lp.split("-")
    out = {}
    for i in range(1, len(parts) + 1):
        out.update(strings.get("-".join(parts[:i]), {}))
    return out

def resolve_base(strings, wanted, app=None):
    """The table the flow's language lives in: `wanted` (default en), else its regional variant (en-GB only),
    else the app's development language. Fail with the fix if none fits."""
    if wanted in strings: return wanted
    regional = sorted(lp for lp in strings if lp.split("-")[0] == wanted)
    if regional: return regional[0]
    dev = plist_value(Path(app) / "Info.plist", "CFBundleDevelopmentRegion") if app else ""
    raise Fail(f"the app has no {wanted} strings" + (f" (it's developed in {dev})" if dev else "") +
               ". Set base_locale in the config to the language your flow is written in"
               + (f", e.g. base_locale = \"{dev}\"" if dev in strings else ""))

# System dialogs (permission prompts) are drawn in the device language, which stays English: an app running in
# German still gets "Allow While Using App" (measured on iOS 27 with Maps). Taps on these keep their English text as
# an alternative to any translation, so "Allow" matches the system's dialog and the app's own "Erlauben" button.
SYSTEM_BUTTONS = {"Allow", "Don’t Allow", "Allow Once", "Allow While Using App", "Always Allow", "Change to Always Allow",
                  "Keep Only While Using", "Ask App Not to Track", "Allow Full Access", "Allow All Photos", "Select Photos",
                  "Limit Access…", "Allow Access to All Photos", "OK", "Cancel", "Not Now",  # iOS (TCC, CoreLocation, "Save Password?" after a login form)
                  "While using the app", "Only this time", "Don’t allow", "Allow all", "Allow limited access"}  # Android

def override_pattern(overrides, text):
    """The regex a user-set [overrides.<locale>] gives for this English text, or None. `re:` prefixes a regular expression."""
    pats = [(o[text][3:] if o[text].startswith("re:") else regex_literal(o[text])) for o in (overrides or []) if text in o]
    return None if not pats else pats[0] if len(pats) == 1 else "(" + "|".join(dict.fromkeys(pats)) + ")"

def translate_flow(flow, base, target, overrides=None):
    """Rewrite English text selectors to the target language. Returns (flow, untranslated selectors, collisions).
    overrides: a list of {English text: wanted text} dicts, one per target language, that win over the app's strings."""
    by_text = {}
    for k, v in base.items():
        by_text.setdefault(v, []).append(k)
    targets = target if isinstance(target, list) else [target]  # several: match any of their translations
    missing, lines, collisions = [], [], []
    formats = [(k, re.compile("^" + format_regex(v) + "$", re.S)) for k, v in base.items() if has_format(v)]

    def tr_format(text):
        """'Round 2 of 12' -> every target form of the matching format, filled with 2 and 12."""
        for k, rx in formats:
            if m := rx.match(text):
                family = k.split("#")[0]
                forms = {fill_format(v, m.groupdict()) for tg in targets for o, v in tg.items()
                         if o == k or o.split("#")[0] == family and "#" in o}
                forms.discard(None)
                if forms: return sorted(forms)
        return None

    def tr(raw):
        """Translated YAML value for one selector value, or None to leave it as it is."""
        text = yaml_unquote(raw)
        if (pat := override_pattern(overrides, text)) is not None: return yaml_single_quote(pat)
        if text not in by_text and (m := WRAPPED_RE.match(text)) and (m[1] or m[3]):
            # ".*Register", "Self-hosted.*": Flutter and others merge a row's texts into one label ("Title\nDetail"), so a flow
            # matches the part it knows; translate that part and keep the wildcard
            inner = tr(yaml_single_quote(m[2]))
            return None if inner is None else "'" + (m[1] or "") + inner[1:-1] + (m[3] or "") + "'"
        keys = by_text.get(text) or by_text.get(text.replace("'", "\u2019"))
        system = text.replace("'", "\u2019") in SYSTEM_BUTTONS
        if not keys and system:  # the OS's own dialog: stays English (iOS spells it with a curly apostrophe)
            return yaml_single_quote(text.replace("'", "\u2019")) if "'" in text else None
        if not keys:
            forms = tr_format(text)
            if forms is None:
                missing.append(text); return None
            pattern = "|".join(map(regex_literal, forms))  # any plural form: no per-language plural rules needed
            return yaml_single_quote(pattern if len(forms) == 1 else f"({pattern})")
        cands = sorted({tg.get(k, text) for tg in targets for k in keys} | ({text} if system else set()))
        if cands == [text] and regex_literal(text) == text:
            return None
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
        return yaml_single_quote(pattern if len(cands) == 1 else f"({pattern})")

    for line in flow.splitlines():
        m = SELECTOR_RE.match(line)
        if not m:
            lines.append(line); continue
        prefix, raw = m.groups()
        raw, comment = split_comment(raw)
        if raw.startswith("{") and raw.endswith("}"):  # inline map: { text: "Accept", optional: true }
            raw = INLINE_RE.sub(lambda g: g.group(1) + (tr(g.group(2).strip()) or g.group(2)) + g.group(3), raw)
            lines.append(prefix + raw + comment); continue
        if not raw or raw.startswith(("{", "[", "&", "*")):  # map form continues on following lines (text: ...)
            lines.append(line); continue
        new = tr(raw)
        lines.append(line if new is None else prefix + new + comment)
    return "\n".join(lines) + "\n", sorted(set(missing)), sorted(set(collisions))

def yaml_unquote(raw):
    """A YAML scalar's value: 'It''s' -> It's, "Say \\"hi\\"" -> Say "hi", plain stays."""
    if len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        try: return json.loads(raw)
        except ValueError: return raw[1:-1]
    return raw

def split_comment(raw):
    """('"Next"', ' # comment') -- a YAML comment starts at ' #' outside quotes."""
    quote = None
    for i, ch in enumerate(raw):
        if ch in "'\"" and quote in (None, ch): quote = None if quote else ch
        elif ch == "#" and quote is None and (i == 0 or raw[i - 1] in " \t"):
            return raw[:i].rstrip(), " " + raw[i:]
    return raw, ""

def redirect_screenshot(lines, shots_dir):
    """Rewrite one flow line if it names a screenshot, so files land in shots_dir. Handles the scalar
    form ('- takeScreenshot: 01_home') and the map form ('- takeScreenshot:' then '    path: 01_home')."""
    line = lines[-1]
    if m := re.match(r"^(\s*- takeScreenshot:\s*)['\"]?([^'\"#]+?)['\"]?\s*(?:#.*)?$", line):
        lines[-1] = f"{m.group(1)}{yaml_single_quote(str(shots_dir / m.group(2)))}"
    elif m := re.match(r"^(\s*path:\s*)['\"]?([^'\"#]+?)['\"]?\s*(?:#.*)?$", line):
        ind = lambda l: len(l) - len(l.lstrip())
        for prev in reversed(lines[:-1]):  # the step this key belongs to (other keys like cropOn may come first)
            if not prev.strip() or ind(prev) >= ind(line): continue
            if re.match(r"^\s*- takeScreenshot:\s*$", prev):
                lines[-1] = f"{m.group(1)}{yaml_single_quote(str(shots_dir / m.group(2)))}"
            break

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

def with_app_id(flow, app_id):
    """The flow with `appId:` set to this build's id, so one flow serves iOS and Android; a flow of bare steps gets a header."""
    if flow.startswith("---\n") and "\n---\n" not in flow: flow = flow[4:]
    header, sep, body = flow.partition("\n---\n")
    if not sep: header, body = "", flow
    header = re.sub(r"(?m)^appId:.*\n?", "", header).strip("\n")
    return f"appId: {app_id}\n{header}{chr(10) if header else ''}---\n{body}"

def inputs_for(inputs, lproj, defaults_only=False):
    """Text to type for one language: the [inputs] defaults, then [inputs.<locale>] (exact, else the language part: pt for pt-BR)."""
    out = {k: v for k, v in (inputs or {}).items() if isinstance(v, str)}
    if not defaults_only:
        for key in (lproj.split("-")[0], lproj):
            if isinstance(inputs.get(key), dict): out.update(inputs[key])
    return out

def with_env(header, env):
    """The flow header with `env:` values added (merged into an `env:` block the user already wrote), for `inputText: ${name}`."""
    if not env: return header
    lines = header.splitlines()
    new = [f"  {k}: {json.dumps(v, ensure_ascii=False)}" for k, v in env.items()]
    for i, l in enumerate(lines):
        if re.match(r"^env:\s*$", l):
            return "\n".join(lines[:i + 1] + new + lines[i + 1:])
    return "\n".join(lines + ["env:"] + new)

def flow_mapping_lines(text, indent=4):
    """The block-YAML lines for an inline `{ key: value, nested: { a: b }, list: [x, y] }` (launchApp options written on one
    line). Scalars keep their quotes. Raises ValueError on anything that isn't a flow mapping."""
    pos, n = 0, len(text)
    def ws():
        nonlocal pos
        while pos < n and text[pos].isspace(): pos += 1
    def scalar(stops):
        nonlocal pos
        ws(); start = pos
        if pos < n and text[pos] in "\"'":
            q = text[pos]; pos += 1
            while pos < n and text[pos] != q:
                pos += 2 if text[pos] == "\\" and q == '"' else 1
            if pos >= n: raise ValueError("unterminated quote in the launchApp options")
            pos += 1
            return text[start:pos]
        while pos < n and text[pos] not in stops: pos += 1
        return text[start:pos].strip()
    def value():
        nonlocal pos
        ws()
        if pos < n and text[pos] == "{": return mapping()
        if pos < n and text[pos] == "[": return seq()
        return scalar(",}]")
    def mapping():
        nonlocal pos
        pos += 1; out = []
        while True:
            ws()
            if pos < n and text[pos] == "}": pos += 1; return out
            key = scalar(":,}")
            if not key or pos >= n or text[pos] != ":": raise ValueError("write the launchApp options as 'key: value' pairs")
            pos += 1
            out.append((key, value())); ws()
            if pos < n and text[pos] == ",": pos += 1
            elif pos < n and text[pos] != "}": raise ValueError("expected , or } in the launchApp options")
            elif pos >= n: raise ValueError("missing } in the launchApp options")
    def seq():
        nonlocal pos
        pos += 1; out = []
        while True:
            ws()
            if pos < n and text[pos] == "]": pos += 1; return ("seq", out)
            out.append(value()); ws()
            if pos < n and text[pos] == ",": pos += 1
            elif pos >= n: raise ValueError("missing ] in the launchApp options")
    ws()
    if not text.lstrip().startswith("{"): raise ValueError("the launchApp options are not a { ... } mapping")
    tree = mapping(); ws()
    if pos != n: raise ValueError("unexpected text after } in the launchApp options")
    def emit(items, pad):
        lines = []
        for k, v in items:
            if isinstance(v, list) and v: lines += [" " * pad + f"{k}:"] + emit(v, pad + 2)
            elif isinstance(v, list): lines.append(" " * pad + f"{k}: {{}}")
            elif isinstance(v, tuple): lines += [" " * pad + f"{k}:"] + [" " * (pad + 2) + f"- {x}" for x in v[1]]
            else: lines.append(" " * pad + f"{k}: {v}")
        return lines
    return emit(tree, indent)

def localize_flow(flow, lproj, shots_dir, env=None):
    """Make a translated flow self-contained for one locale.

    Maestro can only run several simulators at once from one process (--shard-split), which hands
    any flow to any device. So the language travels with the flow, as launch arguments, not with
    the simulator.
    """
    store = store_code(lproj, APP_STORE) or lproj  # number/date formats follow the store locale
    locale = {"zh-Hans": "zh_CN", "zh-Hant": "zh_TW"}.get(store, store.replace("-", "_"))
    args = [f'      AppleLanguages: "({lproj})"', f'      AppleLocale: "{locale}"']

    def launch(clear, opts=()):
        """A launchApp step with the user's own options (permissions, appId...) plus the language arguments."""
        opts = list(opts)
        top = lambda pat: next((i for i, l in enumerate(opts) if re.match(r"^    " + pat, l)), None)
        lines = ["- launchApp:"]
        if clear and top(r"clearState:") is None: lines.append("    clearState: true")
        i = top(r"arguments:")
        if i is None: return lines + opts + ["    arguments:"] + args
        rest = opts[i].split(":", 1)[1].strip()
        if rest.startswith("{"):  # `arguments: { demo: "1" }` on one line: expand it, then add ours to the block
            opts[i:i + 1] = ["    arguments:"] + flow_mapping_lines(rest, indent=6)
        elif rest: raise ValueError("write launchApp arguments as a block, not inline")
        return lines + opts[:i + 1] + args + opts[i + 1:]

    header, sep, body = flow.partition("\n---\n")
    if not sep:
        raise ValueError("flow needs an 'appId:' header followed by '---'")
    header = with_env(re.sub(r"(?m)^name:.*\n?", "", header).rstrip() + f"\nname: {lproj}", env)
    lines, out, first, started, i = body.splitlines(), [], None, False, 0
    while i < len(lines):
        line = lines[i]; i += 1
        if m := re.match(r"^(\s*)- launchApp:?\s*(.*)$", line):
            opts = []  # the indented block under it, re-indented to 4 spaces
            while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > len(m.group(1))):
                opts.append(lines[i]); i += 1
            pad = min((len(l) - len(l.lstrip()) for l in opts if l.strip()), default=4)
            opts = ["    " + l[pad:] for l in opts if l.strip()]
            inline = re.sub(r"\s+#.*$", "", m.group(2)).strip() if m.group(2) else ""
            if inline.startswith("{"): opts = flow_mapping_lines(inline) + opts  # `launchApp: { permissions: { all: allow } }`
            elif inline: opts = [f"    appId: {inline}"] + opts  # `launchApp: com.example.app`
            if not started: first = opts  # the user's first launch is shotfleet's fresh-state launch
            else: out += [m.group(1) + l for l in launch(clear=False, opts=opts)]  # keep a nested step's indent
            started = True
        else:
            started = started or bool(re.match(r"^\s*-", line))
            out.append(line); redirect_screenshot(out, shots_dir)
            nxt = next((l for l in lines[i:] if l.strip()), "")
            if screenshot_ends(out, nxt): out += pause_after_screenshot(out)
    return header + "\n---\n" + "\n".join(launch(clear=True, opts=first or ()) + out) + "\n"

def screenshot_ends(out, nxt):
    """True when `out` just finished a takeScreenshot step (scalar or map form, any keys): the next step isn't deeper."""
    j = next((k for k in range(len(out) - 1, -1, -1) if re.match(r"^\s*- takeScreenshot:", out[k])), None)
    if j is None: return False
    ind = lambda l: len(l) - len(l.lstrip())
    pad = ind(out[j])
    if any(l.strip() and ind(l) <= pad for l in out[j + 1:]): return False  # something else came after it (or the pause)
    if re.match(r"^\s*- takeScreenshot:\s*$", out[j]) and j == len(out) - 1: return False  # map form: keys follow
    return not nxt.strip() or ind(nxt) <= pad

def pause_after_screenshot(out, ms=1500):
    """A pause while shotfleet reads the screen's text from the app (exact, any script; see capture_texts)."""
    step = next(l for l in reversed(out) if re.match(r"^\s*- takeScreenshot", l))
    pad = step[:len(step) - len(step.lstrip())]
    return [f"{pad}- extendedWaitUntil:", f'{pad}    visible: "__shotfleet_reading_screen__"',
            f"{pad}    timeout: {ms}", f"{pad}    optional: true"]

# ---------- simulators ----------

SIM_TIMEOUT_S, SIM_BOOT_TIMEOUT_S = 300, 900  # a wedged simulator (CoreSimulator stops answering on a Mac under heavy load) must end the run with a fix, not hang it

class Sim:
    def __init__(self, udid): self.udid = udid
    def run(self, *args, check=True):
        t = SIM_BOOT_TIMEOUT_S if args[:1] == ("bootstatus",) else SIM_TIMEOUT_S  # a first boot on a loaded Mac can take minutes
        try: r = sh(["xcrun", "simctl", *args], timeout=t)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"simctl {args[0]} did not answer within {t} s: simulator {self.udid} is not responding. "
                               f"Shut it down with `xcrun simctl shutdown {self.udid}` and run again; if it stays stuck, restart the Mac")
        if check and r.returncode != 0:
            raise RuntimeError(f"simctl {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout

def healthy_installs(pool, k, install):
    """Install the app on the first k simulators of the pool that answer, shutting down any that don't (CoreSimulator
    wedges under heavy load; one dead simulator must not end the run while others work). Returns the pool with the k
    ready simulators first and the dead ones gone; raises when none answers."""
    ready, dead = [], []
    for sim in pool:
        if len(ready) == k: break
        try: install([sim]); ready.append(sim)
        except RuntimeError as e:
            print(f"simulator {sim.udid} stopped answering ({e}); carrying on without it", flush=True)
            dead.append(sim); OUR_SIMS.discard(sim.udid)
            try: sh(["xcrun", "simctl", "shutdown", sim.udid], timeout=60)
            except (OSError, subprocess.TimeoutExpired): pass
    if not ready: raise RuntimeError("no simulator answers any more; restart the Mac or run `xcrun simctl shutdown all` and run again")
    return ready + [s for s in pool if s not in ready and s not in dead]

def run_setup(device, kind, commands):
    """The user's per-device setup commands ([ios] simctl, [android] shell), once per booted device. `device` is a Sim
    or an Emu. An iOS command is `xcrun simctl <args>` with $UDID replaced; an Android one runs as `adb shell <command>`.
    A failing command is a Fail (exit 2) that prints it."""
    for cmd in commands:
        try:
            if kind == "simctl":
                args = [a.replace("${UDID}", device.udid).replace("$UDID", device.udid) for a in shlex.split(cmd)]
                device.run(*args)
            else:
                device.adb("shell", cmd)
        except RuntimeError as e:
            raise Fail(f"[{'ios' if kind == 'simctl' else 'android'}] {kind} command failed, stopping before the run: {e}")

def make_pool(n, device_type, runtime, prefix="shotfleet", simctl=()):
    """Reuse or create n simulators named <prefix>-<i>, boot them, clean the status bar, run the config's [ios] simctl commands."""
    existing = json.loads(sh(["xcrun", "simctl", "list", "devices", "-j"]).stdout)["devices"].get(runtime, [])
    by_name = {d["name"]: d for d in existing if d.get("isAvailable") and d.get("deviceTypeIdentifier", device_type) == device_type}
    for d in existing:  # same name, other device type (config changed): replace it, or screenshots get the wrong size
        if re.fullmatch(re.escape(prefix) + r"-\d+", d["name"]) and d["name"] not in by_name:
            sh(["xcrun", "simctl", "delete", d["udid"]])
    pool = []
    for i in range(n):
        name = f"{prefix}-{i + 1}"
        err = ""
        if name in by_name: udid = by_name[name]["udid"]
        else:
            made = sh(["xcrun", "simctl", "create", name, device_type, runtime])
            udid, err = made.stdout.strip(), made.stderr.strip()
        if not udid:  # e.g. an older Xcode that has no iPhone 17 Pro Max: say why, and where the valid names are
            raise RuntimeError(f"could not create simulator {name} ({device_type}, {runtime})" + (f": {err}" if err else "") +
                               ". Set device_type (valid ones: xcrun simctl list devicetypes) or runtime in the config")
        s = Sim(udid)
        s.run("boot", udid, check=False)  # already-booted is fine
        pool.append(s)
    for s in pool:
        s.run("bootstatus", s.udid, "-b")
        s.run("status_bar", s.udid, "override", "--time", "9:41", "--dataNetwork", "wifi", "--wifiMode", "active",
              "--wifiBars", "3", "--cellularMode", "active", "--cellularBars", "4",
              "--batteryState", "charged", "--batteryLevel", "100")
        OUR_SIMS.add(s.udid)  # a failing setup command must not leave the simulator booted
        run_setup(s, "simctl", simctl)
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

def ios_screen_texts(port, bundle_id):
    """Every label and value on screen, from the Maestro iOS driver's accessibility tree (exact Unicode)."""
    req = urllib.request.Request(f"http://127.0.0.1:{port}/viewHierarchy", method="POST",
                                 data=json.dumps({"appIds": [bundle_id], "excludeKeyboardElements": False}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r: tree = json.loads(r.read())
    texts = []
    def walk(e):
        for k in ("label", "title", "value", "placeholderValue"):
            v = e.get(k)
            if isinstance(v, str) and v.strip() and v.strip() not in texts: texts.append(v.strip())
        for c in e.get("children") or []: walk(c)
    walk(tree.get("axElement", tree))
    return texts

def capture_texts(stop, debug_dir, raw_dir, bundle_id):
    """While Maestro runs: when a screenshot appears in raw/<locale>/, read that screen's text from the driver of the
    simulator running that locale (Maestro's log says which device and port run which flow) and save it next to it
    as <name>.texts.json. The flow pauses 1.5 s after each screenshot for this. `check` prefers these texts to OCR.
    raw_dir is where Maestro 2.0.x writes <locale>/<name>.png; newer Maestro writes it inside debug_dir (see collect_shots)."""
    port_of, done, sizes = {}, set(), {}  # done: (png, mtime): a re-taken screenshot is read again
    pat = re.compile(r"Selected device \S+ using port (\d+) with execution plan ExecutionPlan\(flowsToRun=\[([^\]]*)\]")

    def read(pngs):  # one port: its screenshots in order, so each gets the screen it shows
        for png in pngs:
            try:
                texts = ios_screen_texts(port_of[png.parent.name], bundle_id)
                tmp = png.with_suffix(".texts.tmp")
                tmp.write_text(json.dumps(texts, ensure_ascii=False))
                os.replace(tmp, png.with_suffix(".texts.json"))
            except Exception:
                pass  # no tree: check falls back to OCR for this screenshot

    with ThreadPoolExecutor(8) as pool:  # a slow driver must not hold up the other simulators' reads
        while not stop.is_set():
            for log in Path(debug_dir).rglob("maestro.log"):
                try:
                    if (size := log.stat().st_size) == sizes.get(log): continue  # unchanged since the last tick
                    sizes[log] = size; found = pat.findall(log.read_text(errors="replace"))
                except OSError: continue
                for port, flows in found:
                    for f in flows.split(","): port_of[Path(f.strip()).stem] = port
            by_port = {}
            for png in [*Path(raw_dir).glob("*/*.png"), *Path(debug_dir).glob("**/takeScreenshot/*/*.png")]:
                try: key = (png, png.stat().st_mtime_ns)
                except OSError: continue
                if key in done or png.parent.name not in port_of: continue
                done.add(key); by_port.setdefault(port_of[png.parent.name], []).append(png)
            list(pool.map(read, by_port.values()))
            stop.wait(0.2)

def collect_shots(staging, debug_dir, name, dst):
    """Move the screenshots (and screen texts) of the flow that took `<name>/<shot>` into dst, which is raw/<locale>.
    Flows name a screenshot relative to Maestro's working directory. 2.0.x writes it there, so under staging/<name>/.
    Maestro 2.11 refuses a path outside its own artifact folder ("resolves outside this run's takeScreenshot output
    folder") and writes it under <debug>/.maestro/tests/<run>/<flow>/takeScreenshot/<name>/ instead."""
    dst.mkdir(parents=True, exist_ok=True)
    for src in [Path(staging) / name, *Path(debug_dir).glob(f"**/takeScreenshot/{name}")]:
        if src.is_dir():
            for f in src.iterdir(): shutil.move(str(f), str(dst / f.name))

STALL_S = 900  # default: no new screenshot for 15 minutes means Maestro or a simulator is hung (a flow takes about a minute)

def run_guarded(cmd, timeout, env=None, cwd=None, progress=None, stall_s=STALL_S):
    """subprocess.run, plus a watchdog that kills `simctl diagnose` started under this command.
    Maestro dumps simulator diagnostics after every failed flow; several at once wedge CoreSimulator
    (even `simctl list` hangs). shotfleet keeps Maestro's own screenshots and logs, so they aren't needed.
    `progress` (optional) returns something that changes whenever the run gets somewhere (the newest screenshot's time); when it stays
    the same for `stall_s` seconds the run is killed and TimeoutExpired is raised with `.stalled` set. The overall `timeout` scales with
    the number of languages, so on its own a hung simulator would keep a 19-language run alive for hours (seen: 6 h with no screenshot)."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, cwd=cwd)
    done, stalled = threading.Event(), threading.Event()
    def watch():
        last, since = progress() if progress else None, time.monotonic()
        while not done.wait(min(5, max(0.2, stall_s / 4))):
            ours = descendants(proc.pid)
            for line in sh(["pgrep", "-f", "simctl diagnose"]).stdout.split():
                if int(line) in ours: sh(["kill", "-9", line])
            if progress:
                now = progress()
                if now != last: last, since = now, time.monotonic()
                elif time.monotonic() - since > stall_s:
                    stalled.set()
                    for p in descendants(proc.pid) | {proc.pid}: sh(["kill", "-9", str(p)])
                    return
    threading.Thread(target=watch, daemon=True).start()
    try:
        out, _ = proc.communicate(timeout=timeout)
    except BaseException as e:  # timeout, Ctrl-C, SIGTERM: never leave Maestro and its drivers running
        for p in descendants(proc.pid) | {proc.pid}: sh(["kill", "-9", str(p)])
        partial = proc.communicate()[0] or ""
        if isinstance(e, subprocess.TimeoutExpired): e.output = partial
        raise
    finally:
        done.set()
    if stalled.is_set():
        e = subprocess.TimeoutExpired(cmd, timeout, output=out); e.stalled = True
        raise e
    return subprocess.CompletedProcess(cmd, proc.returncode, out, "")

def newest_screenshot(folder):
    """The newest PNG's modification time under folder (any depth), 0 when there is none: what `run_guarded` watches."""
    try: return max((p.stat().st_mtime for p in Path(folder).rglob("*.png")), default=0)
    except OSError: return 0

def memory_pressure():
    """macOS's memory pressure level ("1" normal, "2" elevated, "4" critical), "" where it can't be read. A cron or CI
    PATH has no /usr/sbin, and Linux may have no sysctl at all: that must not stop a run."""
    for exe in ("sysctl", "/usr/sbin/sysctl"):
        try: return sh([exe, "-n", "kern.memorystatus_vm_pressure_level"]).stdout.strip()
        except OSError: pass
    return ""

def fit_parallel(n):
    """Halve parallelism under memory pressure; refuse when critical. A loaded Mac makes flows time out
    and retries pile on more load."""
    level = memory_pressure()
    if level == "4":
        raise Fail("macOS reports critical memory pressure. Close some apps and run again")
    if level == "2" and n > 1:
        print(f"memory pressure is elevated: using {max(1, n // 2)} devices instead of {n}")
        return max(1, n // 2)
    return n

def mem_available_gb():
    """Linux MemAvailable in GB, None where /proc/meminfo isn't there."""
    try: return next(int(l.split()[1]) for l in Path("/proc/meminfo").read_text().splitlines() if l.startswith("MemAvailable:")) / 1048576
    except (OSError, StopIteration, ValueError, IndexError): return None

def fit_emulators(n):
    """On Linux, no more emulators than the machine can run: each wants about 2 cores and 3 GB. Measured 2026-10-03 on a 2-core,
    7 GB runner (docs/linux.md): one emulator passes the fixture, two put "Process system isn't responding" over every screenshot.
    # ponytail: the 2 cores and 3 GB per emulator are that one data point plus the emulator's own advice, not a fit; check on a 4-core machine.
    Not applied elsewhere: a Mac is limited by memory pressure (fit_parallel), which this does not read."""
    if not sys.platform.startswith("linux") or n <= 1: return n
    cores, gb = os.cpu_count() or 1, mem_available_gb()
    fit = max(1, min(n, cores // 2, int(gb // 3) if gb is not None else n))
    if fit < n: print(f"this machine has {cores} cores and {gb if gb is None else round(gb, 1)} GB of free memory: using {fit} "
                      f"emulator{'s' if fit > 1 else ''} instead of {n} (each wants about 2 cores and 3 GB)")
    return fit

def overload_note(want, n):
    """Why failures on a loaded Mac are probably not the app's: slow simulators time Maestro's simctl calls out."""
    level = memory_pressure()
    if n >= want and level not in ("2", "4"): return ""
    return ("note: this Mac was short of memory" + (f" (used {n} simulators instead of {want})" if n < want else "")
            + ", and failed flows with 'Unknown error' or 'Unable to clear state' usually mean a simulator was too slow to answer."
            + " Close other simulators and apps and rerun the failed languages: shotfleet run --locales <codes>\n")

def flow_parse_note(out):
    """When Maestro could not read a flow, say so: the retry would fail the same way within seconds, and a memory hint would send people
    to close apps while the YAML is what is wrong. "" when no log says 'Parsing Failed'."""
    for log in sorted(Path(out).glob("maestro*.log")):
        try: text = log.read_text(errors="replace")
        except OSError: continue
        if "Parsing Failed" in text:
            m = re.search(r"Parsing Failed\s+(\S+\.ya?ml:\d+)", text)
            return (f"note: Maestro could not read a flow ({m.group(1) if m else 'see the log'}: 'Parsing Failed', {log}). "
                    "Fix that YAML; this is not a slow-simulator problem.\n")
    return ""

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
    if not path.exists(): return {}
    res = {}
    for tc in ET.parse(path).iter("testcase"):
        fail = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
        res[tc.get("name")] = {"ok": fail is None, "seconds": round(float(tc.get("time") or 0)),
                               "error": (fail.get("message") or fail.text or "").strip()[:300] if fail is not None else None}
    return res

def device_type_id(name):
    """'iPad Pro 13-inch (M5)' or a full com.apple.CoreSimulator.SimDeviceType identifier -> the identifier."""
    if name.startswith("com.apple."): return name
    try: listed = sh(["xcrun", "simctl", "list", "devicetypes", "-j"]).stdout
    except OSError: raise Fail(NO_XCRUN)
    types = json.loads(listed or '{"devicetypes": []}')["devicetypes"]
    match = next((t["identifier"] for t in types if t["name"].casefold() == name.casefold()), None)
    if not match: raise Fail(f"no simulator type called {name!r}. List them: xcrun simctl list devicetypes")
    return match

def device_slug(device_type):
    """com.apple...iPad-Pro-13-inch-M5-12GB -> ipad-pro-13-inch-m5-12gb (a folder and simulator-name prefix)."""
    return device_type.rsplit(".", 1)[-1].lower()

def clear_single_run(out):
    """A multi-device run writes out/<device>/; an old single-device run in out/ itself would hide it from device_runs."""
    for f in ("run.json", "check.json"): (out / f).unlink(missing_ok=True)
    shutil.rmtree(out / "raw", ignore_errors=True)

def cmd_run(config_path, only=None, parallel=None, platform=None):
    plats = [platform] if platform else platforms_in(config_path)
    codes = []
    for p in plats:
        if len(plats) > 1: print(f"\n=== {p} ===")
        codes.append(run_platform(config_path, only, parallel, p))
    return max(codes)

NO_HOOKS = False

def run_hook(hooks, event, config, env_extra):
    """Run the user's commands for one event (strings run by /bin/sh in the config's folder, output to stderr).
    Returns (exit code, command) of the first failure, or (0, None). Nothing runs without --no-hooks being absent
    and a [hooks] table the user wrote."""
    cmds = hooks.get(event)
    if NO_HOOKS or not cmds: return 0, None
    env = {**os.environ, **env_extra, "SHOTFLEET_EVENT": event, "SHOTFLEET_VERSION": VERSION, "SHOTFLEET_CONFIG": config}
    for cmd in [cmds] if isinstance(cmds, str) else cmds:
        try:  # output goes to stderr, so `--json` keeps stdout for the report; when stderr is captured (MCP, tests) relay it
            try: sys.stderr.fileno(); sink = {"stdout": sys.stderr}
            except (AttributeError, ValueError, io.UnsupportedOperation): sink = {"capture_output": True, "text": True}
            r = subprocess.run(["/bin/sh", "-c", cmd], cwd=Path(config).parent, env=env, timeout=hooks.get("hook_timeout_s", 600), **sink)
        except subprocess.TimeoutExpired: return 124, cmd
        if "capture_output" in sink: print(r.stdout + r.stderr, end="", file=sys.stderr)
        if r.returncode: return r.returncode, cmd
    return 0, None

def run_platform(config_path, only, parallel, platform):
    platform, cfg, path = load_config(config_path, platform)
    out = path(cfg.get("out", "out")).resolve()
    env = {"SHOTFLEET_PLATFORM": platform, "SHOTFLEET_OUT": str(out), "SHOTFLEET_BUNDLE_ID": cfg.get("bundle_id") or cfg.get("package") or "",
           "SHOTFLEET_LOCALES": ",".join(only or cfg.get("locales") or [])}
    rc, cmd = run_hook(cfg["_hooks"], "before_run", cfg["_config"], env)
    if rc: raise Fail(f"hook before_run failed (exit {rc}): {cmd}")
    code = capture_platform(platform, cfg, path, only, parallel)
    problems = 0  # a multi-device run (out/<device>/) keeps one check.json per device
    for report in [out / "check.json"] + [d / "check.json" for d in device_runs(out)]:
        try: problems += len(json.loads(report.read_text()).get("problems", []))
        except (OSError, ValueError): pass
    rc, cmd = run_hook(cfg["_hooks"], "after_run", cfg["_config"], {**env, "SHOTFLEET_EXIT": str(code), "SHOTFLEET_PROBLEMS": str(problems),
                                                               "SHOTFLEET_REPORT": str(out / "check.json")})
    if rc: print(f"hook after_run failed (exit {rc}): {cmd}", file=sys.stderr)
    return max(code, 1 if rc else 0)

def capture_platform(platform, cfg, path, only, parallel):
    if platform == "android":
        out = path(cfg.get("out", "out")).resolve(); out.mkdir(parents=True, exist_ok=True)
        if devices := cfg.get("devices"):  # phone and tablet sets from one flow: out/<device>/ each
            unknown = [d for d in devices if d not in ANDROID_DEVICES]
            if unknown: raise Fail(f"unknown Android device {', '.join(unknown)}; use {', '.join(ANDROID_DEVICES)}")
            codes = []
            clear_single_run(out)
            for d in devices:
                print(f"\n== {d}")
                (out / d).mkdir(exist_ok=True)
                codes.append(android_run({**cfg, "device": d}, path, out / d, only, parallel))
            return max(codes)
        return android_run(cfg, path, out, only, parallel)
    if devices := cfg.get("device_types"):  # iPhone and iPad sets from one flow: out/<device>/ each
        codes = []
        clear_single_run(path(cfg.get("out", "out")).resolve())
        for d in devices:
            dt = device_type_id(d)
            print(f"\n== {d}")
            codes.append(ios_run({**cfg, "device_type": dt, "sim_prefix": f"shotfleet-{device_slug(dt)}", "multi_device": True,
                                  "out": str(path(cfg.get("out", "out")).resolve() / device_slug(dt))}, path, only, parallel))
        return max(codes + [ipad_set_missing(path(cfg.get("out", "out")).resolve())])
    return ios_run(cfg, path, only, parallel)

def ipad_set_missing(parent):
    """Across a multi-device run (parent/<device>/): an app that runs on iPad needs a 13" iPad set somewhere. 1 if missing."""
    subs = device_runs(parent)
    app = next((json.loads((d / "run.json").read_text()).get("app") for d in subs), None)
    if not app or "2" not in plist_value(Path(app) / "Info.plist", "UIDeviceFamily"): return 0
    if any(apple_class(image_info(p)[0]) == 'iPad 13"' for d in subs for p in (d / "raw").glob("*/*.png")): return 0
    print('the app runs on iPad, so the App Store requires 13" iPad screenshots: add "iPad Pro 13-inch (M5)" to device_types')
    return 1

def shutdown_sims():
    for udid in OUR_SIMS:  # shutting down also clears the status bar override
        try: sh(["xcrun", "simctl", "shutdown", udid], timeout=60)
        except subprocess.TimeoutExpired: print(f"note: simulator {udid} did not shut down within 60 s; run `xcrun simctl shutdown {udid}`", file=sys.stderr)
    OUR_SIMS.clear()

def ios_run(cfg, path, only=None, parallel=None):
    try: return ios_run_inner(cfg, path, only, parallel)
    finally: shutdown_sims()  # a 2nd device's pool must not boot on top of the 1st's

def ios_run_inner(cfg, path, only, parallel):
    cfg = dict(cfg)
    if "device_type" in cfg: cfg["device_type"] = device_type_id(cfg["device_type"])
    cfg.setdefault("device_type", "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max")
    if "runtime" not in cfg: cfg["runtime"] = latest_ios_runtime()  # setdefault would ask xcrun even when the config names one
    cfg["app"] = str(path(cfg["app"]))
    framework_hint(cfg["app"], "strings" in cfg, path("."))
    # default: the strings compiled into the app under test, so selectors always match the binary
    strings = config_strings(cfg, path) or load_strings(Path(cfg["app"]))
    flow = with_app_id(path(cfg["flow"]).read_text().replace("\r\n", "\n"), cfg["bundle_id"])
    base_locale = resolve_base(strings, cfg.get("base_locale", "en"), cfg["app"])
    en = strings[base_locale]
    note_partly_translated(strings, base_locale, only or cfg.get("locales") or None)
    locales = cap_locales(only or cfg.get("locales") or shipped_locales(strings, base_locale))
    out = path(cfg.get("out", "out")).resolve()
    # stale flows, logs and JUnit files from an earlier run must never be read as this run's results;
    # raw/<locale> is cleared per locale below, so a partial rerun keeps the other languages
    for d in ("flows", "debug", "shots"): shutil.rmtree(out / ".work" / d, ignore_errors=True)
    for f in out.glob("junit*.xml"): f.unlink()
    (out / ".work" / "flows").mkdir(parents=True)

    # translate every flow first, so selector problems show up before any simulator boots
    report = {"locales": {}, "config": cfg.get("_config"), **run_strings(cfg, path)}
    for lp in locales:
        if lp not in strings:
            print(f"skip {lp}: app has no {lp}.lproj"); continue
        text, missing, clash = translate_flow(flow, en, with_fallback(strings, lp), [cfg.get("_overrides", {}).get(lp, {})])
        for c in clash: print(f"warning {lp}: {c}; anchor that step (below:/above:) if it taps the wrong element")
        shutil.rmtree(out / "raw" / lp, ignore_errors=True); (out / "raw" / lp).mkdir(parents=True)
        (out / ".work" / "flows" / f"{lp}.yaml").write_text(localize_flow(text, lp, Path(lp), inputs_for(cfg.get("_inputs"), lp)))
        report["locales"][lp] = {"untranslated_selectors": missing}
    print_untranslated(report)

    if not report["locales"]:
        raise Fail(f"none of those languages are in the app. It ships: {', '.join(shipped_locales(strings, base_locale))} "
                   "(write them as listed; case and region matter)")
    want = min(parallel or cfg.get("parallel", 4), len(report["locales"]))
    n = fit_parallel(want)
    print(f"booting {n} simulators ({cfg['device_type'].split('.')[-1]}, {cfg['runtime'].split('.')[-1]})")
    pool = make_pool(n, cfg["device_type"], cfg["runtime"], cfg.get("sim_prefix", "shotfleet"), cfg.get("simctl", ()))
    OUR_SIMS.update(s.udid for s in pool)
    kill_stale_drivers()
    def install(sims):  # each flow's clearState gives every locale a fresh start
        for sim in sims:
            sim.run("terminate", sim.udid, cfg["bundle_id"], check=False)
            sim.run("uninstall", sim.udid, cfg["bundle_id"], check=False)
            sim.run("install", sim.udid, cfg["app"])
    pool[:] = healthy_installs(pool, len(pool), install)
    n = len(pool)

    expected = count_screenshots(flow)

    def batch(lps, attempt):
        """Run these locales in one sharded Maestro process; return {lproj: result}."""
        flows_dir = out / ".work" / "flows" / f"attempt{attempt}"
        flows_dir.mkdir(parents=True)
        staging, debug = out / ".work" / "shots" / f"attempt{attempt}", out / ".work" / "debug" / f"attempt{attempt}"
        staging.mkdir(parents=True)  # the flows' screenshot names are relative to this (Maestro's working directory)
        for lp in lps: shutil.copy(out / ".work" / "flows" / f"{lp}.yaml", flows_dir)
        k = min(n, len(lps))
        junit = out / f"junit{attempt}.xml"; junit.unlink(missing_ok=True)
        env = {**os.environ, **java_env(), "MAESTRO_DRIVER_STARTUP_TIMEOUT": "240000", "MAESTRO_CLI_NO_ANALYTICS": "1"}  # 4 drivers starting at once are slow
        stop = threading.Event()
        reader = threading.Thread(target=capture_texts, daemon=True,
                                  args=(stop, debug, staging, cfg["bundle_id"]))
        reader.start()
        try:
            r = run_guarded([maestro_cmd() or "maestro", "--device", ",".join(s.udid for s in pool[:k]), "test", str(flows_dir),
                             "--shard-split", str(k), "--format", "JUNIT", "--output", str(junit),
                             "--debug-output", str(debug)],
                            env=env, timeout=cfg.get("timeout_s", 600) * -(-len(lps) // k) + 300, cwd=staging,
                            progress=lambda: max(newest_screenshot(staging), newest_screenshot(debug), newest_screenshot(out / "raw")),
                            stall_s=cfg.get("stall_s", STALL_S))
            (out / f"maestro{attempt}.log").write_text(r.stdout + r.stderr)
        except subprocess.TimeoutExpired as e:
            (out / f"maestro{attempt}.log").write_text(e.output or "")
            print(f"maestro made no new screenshot for {cfg.get('stall_s', STALL_S)} s and was stopped (a hung simulator or flow; log: {out / f'maestro{attempt}.log'})"
                  if getattr(e, "stalled", False) else f"maestro timed out (log: {out / f'maestro{attempt}.log'})")
        finally:
            stop.set(); reader.join(timeout=10)
            kill_stale_drivers()
        for lp in lps: collect_shots(staging, debug, lp, out / "raw" / lp)
        res = junit_results(junit)
        out_ = {}
        for lp in lps:
            shots = len(list((out / "raw" / lp).glob("*.png")))
            # Maestro skips its report when a shard crashes; the screenshots on disk are the ground truth then
            r_ = res.get(lp) or {"ok": shots == expected, "error": None if shots == expected else "no result (see maestro log)"}
            if r_["ok"] and shots != expected:
                r_ = {**r_, "ok": False, "error": f"flow passed but took {shots} of {expected} screenshots"}
            if r_["ok"] and (note := blank_note(out / "raw" / lp)):
                r_ = {**r_, "ok": False, "error": note}
            out_[lp] = {**r_, "ok": r_["ok"] and shots == expected, "screenshots": shots, "attempts": attempt}
        return out_

    print(f"capturing {len(report['locales'])} locales on {n} simulators...", flush=True)
    t0 = time.time()
    final = batch(list(report["locales"]), 1)
    retry = [lp for lp, r_ in final.items() if not r_["ok"]]
    if retry:  # simulators and drivers flake; one retry of just the failures is cheap
        print(f"retrying {len(retry)}: {', '.join(retry)}", flush=True)
        for lp in retry: shutil.rmtree(out / "raw" / lp); (out / "raw" / lp).mkdir()
        # Maestro's clearState uninstalls and reinstalls the app; when a slow simulator makes that time out halfway,
        # the app is gone and every flow of the retry would fail within seconds ("Unknown error")
        pool[:] = healthy_installs(pool, min(n, len(retry)), install)  # a simulator that stopped answering is left out
        n = len(pool)
        final.update(batch(retry, 2))
    results = []
    for lp, r_ in final.items():
        print_result(lp, r_, expected)
        results.append({"lproj": lp, **r_})
    if not all(r["ok"] for r in results): print(flow_parse_note(out) or overload_note(want, n), end="")
    for r in results: report["locales"][r["lproj"]].update(r)
    report["wall_seconds"] = round(time.time() - t0)
    report["simulators"] = n
    report["app"] = cfg["app"]
    (out / "run.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"captured {sum(r['ok'] for r in results)}/{len(results)} locales in {report['wall_seconds']}s on {n} simulators")
    failed = [r["lproj"] for r in results if not r["ok"]]
    if not any((out / "raw").glob("*/*.png")):
        print("no screenshots were captured, so there's nothing to check; see the errors above and the maestro logs")
        return 1
    return max(cmd_check(out, strings, ipad_rule=not cfg.get("multi_device"), expect=cfg.get("_expect")), 1 if failed else 0)

# ---------- android ----------

BREW = Path("/opt/homebrew")
SDK_PARTS = ("platform-tools", "emulator", "cmdline-tools", "build-tools", "system-images")

def host_abi(machine=None):
    """The emulator image architecture that runs at full speed here: arm64 on Apple silicon and ARM Linux, x86_64 elsewhere."""
    return "arm64-v8a" if (machine or host_platform.machine()).lower() in ("arm64", "aarch64") else "x86_64"

ABI = host_abi()
DEFAULT_IMAGE = f"system-images;android-36;google_apis;{ABI}"

SYSTEM_SDKS = (Path("/usr/lib/android-sdk"),)  # where Debian and Ubuntu packages put an SDK

def clean_path(p):
    """An absolute path with ~ expanded and any `..` or `.` folded away. Google's Android CLI (the new sdkmanager) refuses to unpack into a folder named
    like /work/app/../Android/Sdk ("Illegal entry path escaping destination directory"), found on a GitHub runner on 2026-10-03."""
    return Path(os.path.abspath(os.path.expanduser(str(p))))

def find_sdk(env=None):
    """The Android SDK, first match of: ANDROID_HOME, ANDROID_SDK_ROOT, ~/Library/Android/sdk, Homebrew's
    android-commandlinetools, the folder above an `adb` on the PATH. A match has at least one SDK folder in it.
    Nothing found: ANDROID_HOME (or the Android Studio default), so messages still name a place."""
    env = os.environ if env is None else env
    cands = [env.get("ANDROID_HOME"), env.get("ANDROID_SDK_ROOT"), Path.home() / "Library/Android/sdk",
             Path.home() / "Android/Sdk", Path.home() / "Android/sdk", *SYSTEM_SDKS,  # Android Studio and Debian on Linux
             BREW / "share/android-commandlinetools",
             *sorted((BREW / "Caskroom/android-commandlinetools").glob("*"), reverse=True)]
    if adb := shutil.which("adb", path=env.get("PATH", "")):
        adb = Path(adb).resolve()
        if adb.parent.name == "platform-tools": cands.append(adb.parent.parent)
    for c in filter(None, cands):
        if any((Path(c) / part).is_dir() for part in SDK_PARTS): return clean_path(c)
    return clean_path(env.get("ANDROID_HOME") or Path.home() / ("Library/Android/sdk" if sys.platform == "darwin" else "Android/Sdk"))  # not is_mac(): SDK = find_sdk() below runs at import, before is_mac exists

SDK = find_sdk()

def cmdline_tool(name, sdk=None):
    """sdkmanager or avdmanager: the SDK's cmdline-tools (latest, else any version), else on the PATH, else Homebrew's. Or None."""
    sdk = sdk or SDK
    for p in (sdk / "cmdline-tools/latest/bin" / name, *sorted((sdk / "cmdline-tools").glob(f"*/bin/{name}"), reverse=True),
              Path(shutil.which(name) or "/nonexistent"), BREW / "bin" / name):
        if p.is_file(): return p

def find_image(sdk=None, abi=None):
    """Package id of the best installed image of API 33+ for this machine's architecture (per-app languages need 33), or
    None: newest API first, google_apis before google_apis_playstore."""
    sdk, best = sdk or SDK, []
    for d in (sdk / "system-images").glob(f"android-*/google_apis*/{abi or ABI}"):
        api = re.fullmatch(r"android-(\d+)(?:\.(\d+))?", d.parent.parent.name)
        if api and int(api[1]) >= 33 and any((d / f).is_file() for f in ("package.xml", "source.properties")):
            best.append(((int(api[1]), int(api[2] or 0), d.parent.name == "google_apis"), f"system-images;{d.parent.parent.name};{d.parent.name};{abi or ABI}"))
    return max(best)[1] if best else None

def sdkmanager_commands(packages, sdk=None):
    """The exact shell commands that install these SDK packages with the sdkmanager that exists (or Homebrew's, installed
    first), with JAVA_HOME in front when Java is keg-only."""
    sdk = sdk or SDK
    tool, cmds = cmdline_tool("sdkmanager", sdk), []
    java = f"JAVA_HOME={shlex.quote(java_env()['JAVA_HOME'])} " if java_env().get("JAVA_HOME") else ""
    if not tool and not is_mac():  # no Homebrew cask: Google's zip goes to <sdk>/cmdline-tools/latest
        tool = sdk / "cmdline-tools/latest/bin/sdkmanager"
        cmds += [f"# download 'Command line tools only' from https://developer.android.com/studio#command-line-tools-only and unzip it "
                 f"so that {tool} exists",
                 f"yes | {java}{shlex.quote(str(tool))} --sdk_root={shlex.quote(str(sdk))} --licenses"]
    elif not tool:
        tool = BREW / "share/android-commandlinetools/cmdline-tools/latest/bin/sdkmanager"
        cmds += ["brew install --cask android-commandlinetools", f"yes | {java}{shlex.quote(str(tool))} --licenses"]
    known = any((sdk / part).is_dir() for part in SDK_PARTS)
    root = f"--sdk_root={shlex.quote(str(sdk))} " if known and sdk not in tool.parents else ""
    return cmds + [f"{java}{shlex.quote(str(tool))} {root}" + " ".join(shlex.quote(p) for p in packages)]

def commands_text(cmds):
    """sdkmanager_commands() inside a sentence: a '# ...' line is an instruction (Linux: where Google's zip goes), and pasted after
    'with:' it would turn the whole line into a comment, so it is said first."""
    notes = [c.lstrip("# ") for c in cmds if c.startswith("#")]
    return ("; ".join(notes) + ", then run: " if notes else "") + "; ".join(c for c in cmds if not c.startswith("#"))

def adb_cmd():
    """adb from the SDK we found, else whatever is on the PATH."""
    adb = SDK / "platform-tools/adb"
    return str(adb) if adb.is_file() else "adb"

def android_env():
    """What Maestro needs to find the SDK we chose: ANDROID_HOME, and its adb on the PATH."""
    path = {**os.environ, **java_env()}.get("PATH", "")
    return {"ANDROID_HOME": str(SDK), "PATH": f"{SDK / 'platform-tools'}:{path}" if adb_cmd() != "adb" else path}

DEMO_MODE = [  # no ANR or crash dialogs over the screenshot, no animations (a slow machine shows "Process system isn't responding" otherwise); then SystemUI demo mode: fixed clock, full battery and signal, no notification icons
    "settings put global hide_error_dialogs 1",
    "settings put global window_animation_scale 0",
    "settings put global transition_animation_scale 0",
    "settings put global animator_duration_scale 0",
    "settings put global sysui_demo_allowed 1",
    "am broadcast -a com.android.systemui.demo -e command enter",
    "am broadcast -a com.android.systemui.demo -e command clock -e hhmm 0941",
    "am broadcast -a com.android.systemui.demo -e command battery -e level 100 -e plugged false",
    "am broadcast -a com.android.systemui.demo -e command network -e wifi show -e level 4 -e fully true",
    "am broadcast -a com.android.systemui.demo -e command network -e mobile hide",  # "datatype none" still showed 3G
    "am broadcast -a com.android.systemui.demo -e command notifications -e visible false",
]

class Emu:
    def __init__(self, port): self.port, self.serial, self.proc = port, f"emulator-{port}", None  # proc: the emulator process shotfleet started
    def adb(self, *args, check=True, timeout=180):
        r = sh([adb_cmd(), "-s", self.serial, *args], timeout=timeout)
        if check and r.returncode != 0:
            raise RuntimeError(f"adb {' '.join(args)}: {(r.stderr or r.stdout).strip()}")
        return r.stdout
    def booted(self):
        """sys.boot_completed is 1 AND the package service answers: on a busy machine the first can be true while `adb install`
        still says "Can't find service: package" (seen with two emulators on 2 cores)."""
        if sh([adb_cmd(), "-s", self.serial, "shell", "getprop", "sys.boot_completed"], timeout=15).stdout.strip() != "1": return False
        return "Service package: found" in sh([adb_cmd(), "-s", self.serial, "shell", "service", "check", "package"], timeout=15).stdout

SNAPSHOT = "shotfleet"

def start_emu(avd, port, read_only=True, snapshot=False):
    """Headless emulator. Read-only copies boot from the saved snapshot (4-5 s instead of ~22 s cold, measured)."""
    boot = ["-snapshot", SNAPSHOT, "-no-snapshot-save"] if snapshot else ["-no-snapshot"]
    EMU_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = EMU_LOG_DIR / f"emulator-{port}.log"
    with log.open("wb") as f:  # the child keeps its own copy of the handle
        p = subprocess.Popen([str(SDK / "emulator/emulator"), "-avd", avd, "-port", str(port), "-no-window", "-no-audio",
                              "-no-boot-anim"] + boot + (["-read-only"] if read_only else []),
                             stdout=f, stderr=subprocess.STDOUT, env={**os.environ, "ANDROID_AVD_HOME": str(avd_home())})
    p.log_path = log
    return p

EMU_LOG_DIR = Path(tempfile.gettempdir()) / "shotfleet-emulator-logs"

def emulator_log_tail(proc, lines=15):
    """The last lines of an emulator's own output, for a failure message ('' when there is none)."""
    try: text = Path(proc.log_path).read_text(errors="replace")
    except (AttributeError, OSError): return ""
    return "\n".join([l for l in text.splitlines() if l.strip()][-lines:])

def boot_failure_hint(output=""):
    """The likely cause of an emulator that did not boot. `output` is the emulator's own last lines: some fatal messages name the fix exactly."""
    if "Not enough space to create userdata partition" in output:
        return ("the emulator wants about 12 GB free for its data partition (see the FATAL line above): free disk space, or set a smaller "
                "disk.dataPartition.size in ~/.android/avd/<name>.avd/config.ini; GitHub's hosted Linux runners start with about 7 GB free, so clear "
                "/usr/local/lib/android and /usr/share/dotnet first")
    if sys.platform.startswith("linux") and not (os.access("/dev/kvm", os.R_OK) and os.access("/dev/kvm", os.W_OK)):
        return "this machine has no usable /dev/kvm, so the emulator is far too slow (docs/linux.md); Android runs need hardware virtualization"
    return "each emulator wants about 3 GB of free memory and 2 CPU cores; lower `parallel` in the config, or free memory, and run again"

def wait_booted(emus, timeout=600):
    """Wait until every emulator reports sys.boot_completed. Fails at once, with the emulator's own output, when its process exits;
    on a timeout the message carries the last lines of each emulator's log and the likely cause."""
    t0 = time.time()
    while not all(e.booted() for e in emus):
        for e in emus:
            proc = getattr(e, "proc", None)
            if proc is not None and proc.poll() is not None:
                raise RuntimeError(f"{e.serial}: the emulator exited with code {proc.returncode} before it booted.\n"
                                   f"its output ({getattr(proc, 'log_path', 'not kept')}):\n{emulator_log_tail(proc)}\n{boot_failure_hint(emulator_log_tail(proc))}")
        if time.time() - t0 > timeout:
            tails = "\n".join(f"{e.serial} ({getattr(e.proc, 'log_path', 'no log')}):\n{emulator_log_tail(e.proc)}" for e in emus if getattr(e, "proc", None) is not None)
            raise RuntimeError(f"emulators did not boot in time ({timeout} s).\n{tails}\n{boot_failure_hint(tails)}")
        time.sleep(3)

# Exactly 9:16 at 1080px+ so Google Play can recommend the listing (research/store-specs.md)
ANDROID_DEVICES = {
    "phone": {"avd": "shotfleet_android", "profile": "pixel_5", "size": (1080, 1920, 420), "folder": "phoneScreenshots"},
    "tablet": {"avd": "shotfleet_android_tablet", "profile": "pixel_tablet", "size": (1440, 2560, 320),
               "folder": "tenInchScreenshots"},
    # 1080 px at 280 dpi is 617 dp wide: sw600dp, the 7" layout bucket. Not the Nexus 7's 1200x1920 (10:16, not 9:16)
    "tablet-7": {"avd": "shotfleet_android_tablet7", "profile": "7in WSVGA (Tablet)", "size": (1080, 1920, 280),
                 "folder": "sevenInchScreenshots"},
}

def avd_home():
    """Where shotfleet keeps its emulators: ANDROID_AVD_HOME, ANDROID_USER_HOME/avd, else ~/.android/avd. Named explicitly to avdmanager
    and the emulator, because on a Linux box that sets XDG_CONFIG_HOME (GitHub's runners do) they would otherwise use ~/.config/.android."""
    env = os.environ
    if env.get("ANDROID_AVD_HOME"): return Path(env["ANDROID_AVD_HOME"])
    return (Path(env["ANDROID_USER_HOME"]) if env.get("ANDROID_USER_HOME") else Path.home() / ".android") / "avd"

def android_pool(n, cfg, pool):
    """Boot n read-only copies of one AVD (created on first use as a 1080x1920 phone) into `pool`.
    The caller owns `pool` and kills it in a finally, so emulators never outlive a failed boot."""
    device = cfg.get("device", "phone")
    kind = ANDROID_DEVICES[device]
    avd = cfg.get("avd" if device == "phone" else f"avd_{device}", kind["avd"])  # `avd` names the phone emulator
    avd_dir = avd_home() / f"{avd}.avd"
    if not avd_dir.exists():
        image = cfg.get("system_image") or find_image() or DEFAULT_IMAGE
        avdmanager = cmdline_tool("avdmanager")
        if not avdmanager:
            raise Fail(f"avdmanager not found under {SDK}/cmdline-tools. Install it with: " + commands_text(sdkmanager_commands(["cmdline-tools;latest"])))
        avd_home().mkdir(parents=True, exist_ok=True)  # avdmanager refuses a named folder that does not exist
        r = sh([str(avdmanager), "create", "avd", "-n", avd, "-k", image, "-d", kind["profile"]], input="no\n",
               env={**os.environ, **java_env(), "ANDROID_AVD_HOME": str(avd_home())})
        if r.returncode != 0 or not (avd_dir / "config.ini").exists():
            detail = " ".join(l.strip() for l in (r.stderr + r.stdout).splitlines() if l.strip() and not l.startswith("["))[-300:]  # not inside the f-string: Python 3.11 rejects nested quotes there
            raise Fail(f"couldn't create the emulator {avd} from {image}: {detail}. "
                       f"Install the image with: {commands_text(sdkmanager_commands([image]))} (or set system_image in the config)")
        ini = avd_dir / "config.ini"
        w, h, dpi = kind["size"]
        ini.write_text(re.sub(r"(?m)^hw\.lcd\.width=.*", f"hw.lcd.width={w}",
                       re.sub(r"(?m)^hw\.lcd\.height=.*", f"hw.lcd.height={h}",
                       re.sub(r"(?m)^hw\.lcd\.density=.*", f"hw.lcd.density={dpi}", ini.read_text()))))
    if not (avd_dir / "snapshots" / SNAPSHOT).exists():  # one-time: boot writable, save a snapshot copies start from
        e = Emu(5700); p = e.proc = start_emu(avd, e.port, read_only=False); pool.append(e)  # killed by the caller if this fails
        wait_booted([e]); time.sleep(20)
        e.adb("emu", "avd", "snapshot", "save", SNAPSHOT, check=False)
        e.adb("emu", "kill", check=False); p.wait(timeout=120)
        pool.remove(e)
    snap = (avd_dir / "snapshots" / SNAPSHOT).exists()
    for i in range(n):
        e = Emu(5702 + 2 * i)
        if e.booted(): raise Fail(f"{e.serial} is already running. Stop it (adb -s {e.serial} emu kill) and run again")
        e.proc = start_emu(avd, e.port, snapshot=snap); pool.append(e)
        time.sleep(2)  # staggered starts avoid adb port races
    wait_booted(pool)
    for e in pool:
        for c in DEMO_MODE: e.adb("shell", c, check=False)
        run_setup(e, "shell", cfg.get("shell", ()))  # after boot, every run: the snapshot boot discards properties

VARS_JS = "shotfleet_vars.js"

def android_vars(inputs, lang):
    """(JS text, names) for the per-emulator typed values of one Android round, or ("", set()) when no [inputs.<locale>] exists.
    `lang` is {emulator serial: language}. Maestro hands any flow to any emulator, so the flow asks the emulator who it is:
    the script picks its row by MAESTRO_DEVICE_UDID. Without that variable (Maestro 2.0.10 has none) it types the
    [inputs] defaults, the first language's value for a name that has no default."""
    names = {k for v in (inputs or {}).values() if isinstance(v, dict) for k in v}
    if not names: return "", set()
    rows = {s: {k: v for k, v in inputs_for(inputs, lp).items() if k in names} for s, lp in lang.items()}
    fallback = {**next(iter(rows.values())), **{k: v for k, v in inputs_for(inputs, "", defaults_only=True).items() if k in names}}
    # ponytail: the map holds this round's emulators only (one row each), regenerated per round
    return ("// written by shotfleet: [inputs.<locale>] per emulator\noutput.v = (function () {\n"
            f"  var byDevice = {json.dumps(rows)};\n  var fallback = {json.dumps(fallback)};\n"
            '  var udid = typeof MAESTRO_DEVICE_UDID === "undefined" ? "" : String(MAESTRO_DEVICE_UDID);\n'
            '  if (!byDevice[udid] && typeof console !== "undefined") console.log("shotfleet: no row for device \'" + udid + "\'; typing the [inputs] defaults");\n'
            "  return byDevice[udid] || fallback;\n})();\n"), names

def android_flow(text, name, shots_dir, env=None, mapped=()):
    """Per-run copy of a translated flow: own name, own screenshot folder, starts with a plain launchApp.
    No clearState: on Android it wipes the per-app language shotfleet just set; shotfleet clears data itself.
    `mapped` names (see android_vars) are read from the script's output.v, after a runScript step at the top."""
    header, sep, body = text.partition("\n---\n")
    if not sep: raise ValueError("flow needs an 'appId:' header followed by '---'")
    header = with_env(re.sub(r"(?m)^name:.*\n?", "", header).rstrip() + f"\nname: {name}", env)
    if mapped:
        body = re.sub(r"\$\{(%s)\}" % "|".join(map(re.escape, sorted(mapped))), r"${output.v.\1}", body)
    first = next((l for l in body.splitlines() if l.strip() and not l.strip().startswith("#")), "")
    out = [f"- runScript: {VARS_JS}"] if mapped else []
    if not re.match(r"\s*- launchApp", first): out.append("- launchApp")
    # ponytail: no screen-text reading on Android: `maestro hierarchy` can't reach the drivers of a sharded run and
    # tears down its port forwards, which hung the run (measured 2026-10-01); Android screenshots are checked with OCR
    for line in body.splitlines():
        if re.match(r"^\s*clearState:", line): continue
        if m := re.match(r"^(\s*)- launchApp:\s*(\{.*\})\s*(?:#.*)?$", line):  # one-line options: expand, so clearState can be dropped
            out.append(f"{m.group(1)}- launchApp:")
            out += [m.group(1) + l for l in flow_mapping_lines(m.group(2)) if not re.match(r"^    clearState:", l)]
            continue
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
    framework_hint(apk, "strings" in cfg, path("."))
    strings = config_strings(cfg, path) or load_strings_apk(apk, cfg.get("base_locale", "en"))
    base = strings[cfg.get("base_locale", "en")]
    note_partly_translated(strings, cfg.get("base_locale", "en"), only or cfg.get("locales") or None)
    locales = cap_locales(only or cfg.get("locales") or shipped_locales(strings))
    flow = with_app_id(path(cfg["flow"]).read_text().replace("\r\n", "\n"), pkg)
    expected = count_screenshots(flow)
    if any(isinstance(v, dict) for v in cfg.get("_inputs", {}).values()):
        print("note: on Android [inputs.<locale>] values are found by MAESTRO_DEVICE_UDID (Maestro hands any flow to any emulator); "
              "Maestro 2.11.0 sets it; Maestro 2.0.10 doesn't, so on 2.0.10 Android types the [inputs] defaults")
    # stale flows, logs and JUnit files from an earlier run must never be read as this run's results
    for d in ("flows", "tmp", "debug"): shutil.rmtree(out / ".work" / d, ignore_errors=True)
    for f in out.glob("junit*.xml"): f.unlink()
    report = {"locales": {}, "config": cfg.get("_config"), **run_strings(cfg, path)}
    for lp in locales:
        if lp not in strings: print(f"skip {lp}: app has no {lp} strings"); continue
        _, missing, clash = translate_flow(flow, base, with_fallback(strings, lp), [cfg.get("_overrides", {}).get(lp, {})])
        for c in clash: print(f"warning {lp}: {c}; anchor that step (below:/above:) if it taps the wrong element")
        report["locales"][lp] = {"untranslated_selectors": missing}
    print_untranslated(report)
    todo = list(report["locales"])
    if not todo:
        raise Fail(f"none of those languages are in the app. It ships: {', '.join(shipped_locales(strings))} "
                   "(write them as listed; case and region matter)")
    n = fit_emulators(fit_parallel(min(parallel or cfg.get("parallel", 4), len(todo))))
    kind = ANDROID_DEVICES[cfg.get("device", "phone")]
    name = cfg.get("avd" if cfg.get("device", "phone") == "phone" else f"avd_{cfg['device']}", kind["avd"])
    print(f"booting {n} emulators ({name}, {kind['size'][0]}x{kind['size'][1]})", flush=True)
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
            text, _, _ = translate_flow(flow, base, [with_fallback(strings, lp) for lp in lps], [cfg.get("_overrides", {}).get(lp, {}) for lp in lps])
            fdir = out / ".work" / "flows" / tag; fdir.mkdir(parents=True)
            staging = out / ".work" / "tmp" / tag; staging.mkdir(parents=True)  # the flows' screenshot names are relative to this
            vars_js, mapped = android_vars(cfg.get("_inputs"), lang)
            if vars_js: (fdir / VARS_JS).write_text(vars_js)
            for j in range(len(lps)):
                (fdir / f"{tag}_f{j}.yaml").write_text(android_flow(text, f"{tag}_f{j}", Path(f"{tag}_f{j}"), inputs_for(cfg.get("_inputs"), "", defaults_only=True), mapped))
            junit, dbg = out / f"junit_{tag}.xml", out / ".work" / "debug" / tag
            junit.unlink(missing_ok=True); shutil.rmtree(dbg, ignore_errors=True)
            try:
                r = run_guarded([maestro_cmd() or "maestro", "--device", ",".join(e.serial for e in pool[:len(lps)]), "test", str(fdir),
                                 "--shard-split", str(len(lps)), "--format", "JUNIT", "--output", str(junit), "--debug-output", str(dbg)],
                                timeout=cfg.get("timeout_s", 600) + 300, cwd=staging,
                                progress=lambda: max(newest_screenshot(staging), newest_screenshot(dbg)), stall_s=cfg.get("stall_s", STALL_S),
                                env={**os.environ, **java_env(), **android_env(), "MAESTRO_CLI_NO_ANALYTICS": "1",
                                     "MAESTRO_DRIVER_STARTUP_TIMEOUT": "240000"})  # read-only emulators reinstall the driver each boot
                (out / f"maestro_{tag}.log").write_text(r.stdout + r.stderr)
            except subprocess.TimeoutExpired as e:
                print(f"maestro made no new screenshot for {cfg.get('stall_s', STALL_S)} s and was stopped in {tag}" if getattr(e, "stalled", False)
                      else f"maestro timed out in {tag}")
            ran_on, res, results = flow_devices(dbg), junit_results(junit), {}
            for j in range(len(lps)):
                fname, dev = f"{tag}_f{j}", ran_on.get(f"{tag}_f{j}")
                if dev not in lang: continue
                lp = lang[dev]
                dst = out / "raw" / lp
                shutil.rmtree(dst, ignore_errors=True)
                collect_shots(staging, dbg, fname, dst)
                shots = len(list(dst.glob("*.png")))
                r_ = res.get(fname) or {"ok": shots == expected, "error": None if shots == expected else "no result"}
                if r_["ok"] and shots == expected and (note := blank_note(dst)): r_ = {**r_, "ok": False, "error": note}
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
    report.update(wall_seconds=round(time.time() - t0), emulators=n, platform="android", apk=apk,
                  device=cfg.get("device", "phone"))
    (out / "run.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"captured {sum(r_['ok'] for r_ in final.values())}/{len(todo)} locales in {report['wall_seconds']}s on {n} emulators")
    if not any((out / "raw").glob("*/*.png")):
        print("no screenshots were captured, so there's nothing to check; see the errors above and the maestro logs")
        return 1
    return max(cmd_check(out, strings, expect=cfg.get("_expect")), 0 if all(r_["ok"] for r_ in final.values()) else 1)

# ---------- check ----------

def is_mac():
    return sys.platform == "darwin"

def vision_available():
    """macOS text recognition (Vision) exists only on a Mac; elsewhere `check` reads screenshots with Tesseract."""
    return is_mac()

def install_hint(what="tesseract tesseract-lang"):
    return f"brew install {what}" if is_mac() else \
        "apt install tesseract-ocr tesseract-ocr-all (or your distribution's Tesseract packages)"

def ocr_tool():
    if not vision_available(): raise RuntimeError("macOS text recognition is not available on this system")
    if getattr(sys, "frozen", False):  # released build: the helper ships prebuilt inside it
        return str(Path(sys._MEIPASS) / "ocr")
    exe = HERE / ".build" / "ocr"
    src = HERE / "ocr.swift"
    if not exe.exists() or exe.stat().st_mtime < src.stat().st_mtime:
        exe.parent.mkdir(exist_ok=True)
        r = sh(["swiftc", "-O", str(src), "-o", str(exe)])
        if r.returncode != 0: raise RuntimeError("ocr build failed:\n" + r.stderr)
    return str(exe)

TWINS = {"ms": ("id",), "id": ("ms",)}  # language detection can't tell these apart in UI text (measured, tools/langmatrix.py)
LEGACY = {"in": "id", "iw": "he", "ji": "yi", "tl": "fil", "no": "nb"}  # Android's old codes -> what language detection reports

def readable_languages():
    """Base languages the text recognition in use reads. On a Mac (macOS 27: 33 codes, e.g. CJK, Cyrillic, Arabic, Thai, Hindi;
    not Greek, Hebrew, Armenian, Georgian or most Indic and Southeast Asian scripts); elsewhere, what the installed
    Tesseract data covers."""
    if not vision_available():
        have = tesseract_languages()
        return {l for l, t in TESSERACT.items() if t in have} | ({"zh"} if have & {"chi_sim", "chi_tra"} else set())
    return vision_languages()

@functools.cache
def vision_languages():
    return {c.split("-")[0] for c in json.loads(sh([ocr_tool(), "--langs"]).stdout or "[]")}

# Only scripts no other language shares: Cyrillic/Arabic/Han/Devanagari would let Russian pass as Ukrainian
SCRIPTS = {"ja": "[\u3040-\u30ff]", "ko": "[\uac00-\ud7af]", "th": "[\u0e00-\u0e7f]"}

BIDI = dict.fromkeys(map(ord, "\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\u061c\u200b\ufeff"))

@functools.lru_cache(maxsize=None)
def norm(text):
    """Text as OCR and string tables can both agree on: NFKC (NBSP, full-width), no bidi/zero-width marks,
    native digits (Arabic-Indic, Persian, Devanagari...) as ASCII, no accents (OCR drops Hungarian ő), casefolded
    (Android's all-caps buttons), single spaces."""
    t = unicodedata.normalize("NFKD", text.translate(BIDI))
    t = "".join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in t if not unicodedata.combining(c))
    return " ".join(unicodedata.normalize("NFKC", t).casefold().split())

# printf (%d, %1$@, %.1f, %lld), and {name} / {0} placeholders (ICU, Compose, .NET)
SPEC = re.compile(r"%(?:(\d+)\$)?[-+ 0#']*(?:\d+|\*)?(?:\.\d+)?(?:hh|h|ll|l|q|z|t|j|L)?([@dDiuUxXfFeEgGsScCoaAp%])"
                  r"|\{\{\s*(\w+)\s*\}\}|\{(\w+)\}")
NUMBER = r"-?\d[\d.,' \u00a0\u202f]*"

def has_format(text):
    """True for 'Day %d of 15'; false for plain text and for .stringsdict placeholders like '%1$#@jobs@'
    (their plural forms are loaded separately)."""
    return "#@" not in text and any(m.group(2) != "%" for m in SPEC.finditer(text))

def format_regex(fmt, literal=re.escape, named=True):
    """Regex source for what fmt looks like once filled in: numbers for %d, anything for %@ / {name}.
    Groups are named a<arg> (a1, a2... or the placeholder name) so values can be carried to a translation."""
    out, seen, pos, auto = [], set(), 0, 0
    for m in SPEC.finditer(fmt):
        out.append(literal(fmt[pos:m.start()])); pos = m.end()
        if m.group(2) == "%": out.append(literal("%")); continue
        if m.group(1) or m.group(3) or m.group(4): name = m.group(1) or m.group(3) or m.group(4)
        else: auto += 1; name = str(auto)
        group = "a" + re.sub(r"\W", "_", name)
        pat = NUMBER if m.group(2) and m.group(2) in "dDiuUxXfFeEgGaAo" else ".+?"
        if not named: out.append(f"(?:{pat})"); continue
        if group in seen: out.append(f"(?P={group})"); continue
        seen.add(group)
        out.append(f"(?P<{group}>{pat})")
    out.append(literal(fmt[pos:]))
    return "".join(out)

def fill_format(fmt, args):
    """fmt with its placeholders replaced by args ({'a1': '2', 'aname': 'Anna'}); None if an arg is missing."""
    auto = 0
    def sub(m):
        nonlocal auto
        if m.group(2) == "%": return "%"
        if m.group(1) or m.group(3) or m.group(4): name = m.group(1) or m.group(3) or m.group(4)
        else: auto += 1; name = str(auto)
        return args.get("a" + re.sub(r"\W", "_", name), "\0")
    out = SPEC.sub(sub, fmt)
    return None if "\0" in out else out

def norm_piece(text):
    """norm() for a piece of a format string: same folding, but edge spaces kept ("Round " + "%d")."""
    lead, trail = text[:1].isspace(), text[-1:].isspace()
    core = norm(text)
    return (" " if lead and core else "") + core + (" " if trail and core else "")

class Table(frozenset):
    """A locale's normalized strings, plus one regex for its format strings ("day %d of 15")."""
    formats = None

def string_tables(strings):
    """{locale: Table} for judge_screen."""
    tables = {}
    for lp in strings:
        values = with_fallback(strings, lp).values()
        t = Table(norm(v) for v in values)
        pats = [format_regex(v, lambda piece: re.escape(norm_piece(piece)), named=False) for v in values if has_format(v)]
        # "%d" alone matches anything, and "%@ atrás" (pt) matches Spanish "Cuenta atrás": text placeholders need
        # more surrounding words than number placeholders before a match says anything about the language
        pats = [(p, v) for p, v in zip(pats, (v for v in values if has_format(v)))
                if len(re.sub(r"[\W\d_]", "", SPEC.sub("", v))) >= (8 if "(?:.+?)" in p else 3)]
        t.formats = re.compile("^(?:" + "|".join(f"(?:{p})" for p, _ in pats) + ")$") if pats else None
        tables[lp] = t
    return tables

def judge_screen(lp, ocr, tables):
    """(locale the screen shows, problem or None) for one screenshot's OCR result.

    Scores each locale by how many recognized lines are exactly one of its strings: generic language
    detection is unreliable on short UI labels (it reads Russian tab bars as Kazakh)."""
    lines = {n for l in ocr.get("text", "").splitlines() if len(n := norm(l)) > 1}
    score = {o: len(lines & vals) + (sum(1 for l in lines - vals if vals.formats.match(l))
                                      if getattr(vals, "formats", None) else 0)
             for o, vals in tables.items()}
    if ocr.get("ocr") == "external":  # Tesseract joins labels on one visual line ("Alle Übungen WODs"): find them inside
        text = " | ".join(lines)
        for o, vals in tables.items():
            score[o] += sum(1 for v in vals - lines if len(v) >= 5 and re.search(rf"(?<!\w){re.escape(v)}(?!\w)", text))
    best = max(score.values(), default=0)
    got = lp if score.get(lp, 0) == best else max(score, key=score.get)
    if not ocr.get("chars"):
        lang = canon(lp).split("-")[0]
        if LEGACY.get(lang, lang) not in readable_languages() | {"zh"}:
            return None, None  # Hebrew, Georgian, Burmese often read as nothing at all
        return got, "no text found (blank or still loading?)"
    if best < 2:  # one short label ("Training starten" is German and Dutch) proves nothing; use language detection
        c = canon(lp)  # zh-CN -> zh-Hans, zh-HK -> zh-Hant-HK, iw -> he: what language detection reports
        want = ("zh-Hant" if c.startswith("zh-Hant") else "zh-Hans") if c.startswith("zh") else \
            EXPECTED_LANG.get(lp, LEGACY.get(lp.split("-")[0], lp.split("-")[0]))
        if want.split("-")[0] not in readable_languages() | {"zh"}:
            # macOS can't read this script, and the screen shows no other language's strings: not provable either way
            if ocr.get("lang") == "en" and ocr.get("langs", {}).get("en", 0) > 0.9:
                return "en", f"text looks like 'en', expected '{want}'"
            return None, None
        osd = ocr.get("osd_script")  # Tesseract names no language; its script detection is the evidence (see tesseract_script)
        if osd and ocr.get("osd_conf", 0) >= 1.0 and osd not in OSD_SCRIPT.get(want.split("-")[0], (osd,)):
            return None, f"text looks like the {osd} script, expected '{want}'"
        script = SCRIPTS.get(want.split("-")[0])
        if script and len(re.findall(script, ocr.get("text", ""))) >= 3:  # detection mixes up Latin-heavy CJK screens
            return lp, None
        langs = ocr.get("langs", {})
        # short, language-neutral screens ("AMRAP / EMOM / Tabata") get low-confidence guesses: not evidence
        if ocr.get("lang") not in (want, *TWINS.get(want, ())) and langs.get(want, 0) < 0.2 \
                and langs.get(ocr.get("lang"), 0) >= 0.8:
            return ocr.get("lang"), f"text looks like '{ocr.get('lang')}', expected '{want}'"
        return lp, None
    # on a screen with little evidence, one borrowed word ("Round" on a French watch) isn't enough; with plenty,
    # one line is what separates regional variants ("Colour" vs "Color")
    if got != lp and score[got] - score.get(lp, 0) >= (2 if score[got] < 3 else 1):
        return got, f"shows {got} strings ({score[got]} lines) more than {lp} ({score.get(lp, 0)})"
    if got != lp:
        return lp, None
    return got, None

# An Android crash or ANR dialog over the app ("Process system isn't responding" on a slow emulator) is not a store screenshot, whatever
# language the app text under it is in. English only (the emulator's system language), and only where text is read from the picture.
SYSTEM_DIALOG = re.compile(r"isn.?t responding|keeps stopping|has stopped\b", re.I)

def system_dialog(ocr):
    m = SYSTEM_DIALOG.search(ocr.get("text", ""))
    return f'an Android system dialog covers the screen ("{m.group(0)}")' if m else None

def caption_problem(lp, ocr, tables, problem):
    """Framed screenshots carry a marketing caption above the device. Name the common failure plainly
    (a translated caption over an untranslated app)."""
    cap, cap_lang = ocr.get("caption", ""), ocr.get("caption_lang")
    if not cap or not cap_lang: return problem
    c = canon(lp)
    want = ("zh-Hant" if "Hant" in c else "zh-Hans") if c.startswith("zh") else LEGACY.get(c.split("-")[0], c.split("-")[0])
    matches = cap_lang == want or cap_lang in TWINS.get(want, ()) or cap_lang.split("-")[0] == want.split("-")[0] != "zh"
    if problem and problem.startswith("shows ") and matches:
        return f"the caption is in {cap_lang} but the app UI {problem}"
    # ponytail: no "caption in the wrong language" problem on its own: detection misreads short captions
    # ("A WOD timer on your wrist" as Polish); the app's strings are the evidence, the caption only explains it
    return problem

PLAY_FOLDERS = ("phoneScreenshots", "sevenInchScreenshots", "tenInchScreenshots")

def play_folders(folder):
    """Which of Google Play's device folders a supply layout uses (phone, 7" and 10" tablets)."""
    folder = Path(folder)
    return [k for k in PLAY_FOLDERS if any(folder.glob(f"metadata/android/*/images/{k}/*")) or any(folder.glob(f"*/images/{k}/*"))]

def find_screenshots(folder, platform=None, play_folder="phoneScreenshots"):
    """{folder label: [png, ...]} for the layouts people actually have: shotfleet's own output (raw/<locale>),
    fastlane supply (metadata/android/<locale>/images/phoneScreenshots), fastlane deliver (screenshots/<locale>),
    or plain <locale>/ folders."""
    folder = Path(folder)
    if (folder / "screenshots").is_dir() and (folder / "metadata/android").is_dir():
        if platform == "ios": return find_screenshots(folder / "screenshots")
        if platform == "android": return find_screenshots(folder / "metadata" / "android", play_folder=play_folder)
        raise Fail(f"{folder} has both iOS and Android screenshots; check {folder / 'screenshots'} and "
                   f"{folder / 'metadata/android'} separately (each with its own --app)")
    for pattern in ("raw/*/*", f"metadata/android/*/images/{play_folder}/*",
                    f"*/images/{play_folder}/*", "screenshots/*/*", "*/*"):
        found = sorted(p for p in folder.glob(pattern) if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
        if found:
            out = {}
            for png in found:
                label = png.parent.parent.parent.name if png.parent.name == play_folder else png.parent.name
                if re.fullmatch(r"[a-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*", label) or label in CANON:
                    out.setdefault(label, []).append(png)  # not ipad_only/, default/, appleTV/
            return out
    return {}

def app_locale(label, available):
    """The app language a store folder name stands for (de-DE -> de, no -> nb, zh-CN -> zh-Hans, iw-IL -> iw), or None."""
    if label in available: return label
    store = PLAY if label in PLAY else APP_STORE
    for a in sorted(available, key=lambda a: -len(a)):  # most specific first: pt-PT before pt
        if store_code(a, store) == label: return a
    for a in available:  # a folder that isn't a store code, e.g. plain zh-Hans for an app with zh
        if canon(a) == canon(label) or canon(a) == canon(label).split("-")[0]: return a
    return None

OCR_NOTE_AFTER_S = 8  # a first recognition slower than this gets a line saying why the screen is quiet

def warm_up_ocr(ocr, timeout=600):
    """One recognition on its own before the parallel ones, so macOS compiles its model once (minutes after a restart).
    False if it doesn't answer in time: macOS's recognition service (ANECompilerService) is stuck or still compiling.
    It is left running then, so a slow first compile still finishes for the next check."""
    p = subprocess.Popen([ocr, "--warmup"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, start_new_session=True)
    note = threading.Timer(OCR_NOTE_AFTER_S, print, ["macOS is preparing its text recognition, a one-off wait of about 30 seconds "
                                                    "(a few minutes on a busy Mac). Nothing is wrong if this stays quiet."], {"flush": True})
    note.daemon = True; note.start()
    try:
        return bool(p.communicate(timeout=timeout)[0].strip())
    except subprocess.TimeoutExpired:
        return False
    finally:
        note.cancel()

TESSERACT_COMMAND = "tesseract {image} stdout -l {tesseract_with_english}"
# Tesseract starts one OpenMP thread per core; four of them at once spin against each other (measured on 4 cores:
# 73 s for 4 screenshots instead of 2 s), so each process gets one thread unless the user sets the limit.
def tesseract_env():
    return {**os.environ, "OMP_THREAD_LIMIT": os.environ.get("OMP_THREAD_LIMIT", "1")}  # read at call time: PATH may have changed

@functools.cache
def tesseract_languages():
    """Language data Tesseract has installed ({'eng', 'ell', ...}); empty if Tesseract isn't installed."""
    if not shutil.which("tesseract"): return frozenset()
    r = sh(["tesseract", "--list-langs"])
    return frozenset(l.strip() for l in (r.stdout + r.stderr).splitlines()
                     if l.strip() and not l.startswith("List of available languages"))  # the header is on stderr in 4.x

def tesseract_code(lp):
    c = canon(lp); lang = c.split("-")[0]
    return ("chi_tra" if "Hant" in c else "chi_sim") if lang == "zh" else TESSERACT.get(lang, lang)

def screen_text(png):
    """The screen's text as the app reported it during the run (exact, any script), in OCR's result shape; or None."""
    f = Path(png).with_suffix(".texts.json")
    try: texts = [" ".join(t.split()) for t in json.loads(f.read_text())]  # one element per line, as tables are normalized
    except (OSError, ValueError, TypeError, AttributeError): return None  # missing, half-written or not a list
    if not any(texts): return None  # games, canvases and unlabelled UI report nothing at all: OCR the pixels instead
    text = "\n".join(texts)
    return {"text": text, "chars": len(text), "lang": None, "langs": {}, "ocr": "app", "lines": []}

def usable_text(png, tables):
    """screen_text, but only when it proves something: fewer than 2 lines of any language's strings (mostly user content)
    can't tell a wrong-language screen, so those are read by OCR too."""
    t = screen_text(png)
    if t and tables:
        lines = {n for l in t["text"].splitlines() if len(n := norm(l)) > 1}
        if not any(len(lines & vals) >= 2 for vals in tables.values()): return None
    return t

def read_text(ocr, png, timeout=120):
    """OCR one image. Vision can hang on an overloaded Mac, so time out and retry once instead of waiting forever."""
    for _ in range(2):
        try:
            return json.loads(sh([ocr, str(png)], timeout=timeout).stdout or "{}")
        except subprocess.TimeoutExpired:
            pass
    stuck = [l for l in sh(["ps", "-Ao", "pcpu=,comm="]).stdout.splitlines()
             if "ANECompilerService" in l and float(l.split()[0]) > 50]
    raise RuntimeError(f"text recognition hung twice on {png}. " + (
        "macOS's Neural Engine compiler (ANECompilerService) is stuck at full CPU, which blocks all text recognition; "
        "restarting the Mac fixes it" if stuck else "Is the Mac overloaded? Run check again"))

# Tesseract's names for the scripts macOS can't read (for {tesseract} in --ocr-command)
TESSERACT = {"en": "eng", "de": "deu", "fr": "fra", "es": "spa", "it": "ita", "pt": "por", "nl": "nld", "sv": "swe",
             "da": "dan", "no": "nor", "nb": "nor", "fi": "fin", "pl": "pol", "cs": "ces", "ro": "ron", "tr": "tur",
             "ru": "rus", "uk": "ukr", "ar": "ara", "ja": "jpn", "ko": "kor", "th": "tha", "vi": "vie", "hi": "hin",
             "mr": "mar", "id": "ind", "in": "ind", "ms": "msa", "el": "ell", "he": "heb", "iw": "heb", "hy": "hye", "ka": "kat", "bn": "ben", "as": "asm", "gu": "guj",
             "pa": "pan", "ta": "tam", "te": "tel", "kn": "kan", "ml": "mal", "or": "ori", "si": "sin", "km": "khm",
             "lo": "lao", "my": "mya", "am": "amh", "ur": "urd", "fa": "fas", "ne": "nep", "bg": "bul", "mk": "mkd",
             "sr": "srp", "be": "bel", "kk": "kaz", "ky": "kir", "mn": "mon", "hu": "hun", "sk": "slk", "hr": "hrv",
             "sl": "slv", "et": "est", "lv": "lav", "lt": "lit", "is": "isl", "sq": "sqi", "az": "aze", "uz": "uzb",
             "ca": "cat", "eu": "eus", "gl": "glg", "sw": "swa", "zu": "zul", "af": "afr", "fil": "fil", "tl": "tgl"}

OSD_SCRIPT = {"ja": ("Japanese", "Han"), "ko": ("Korean",), "th": ("Thai",)}  # what Tesseract's script detection calls them

def tesseract_script(png, lp):
    """Tesseract's script detection, for listings whose script it reads badly when told the wrong one ({"osd_script": ...}).
    Only for ja, ko and th, and only when installed with its osd data; {} otherwise. Measured on 144 real screenshots: right
    on 142 (the 2 wrong, Korean read as Japanese, scored 0.2 and 0.06), so judge_screen only trusts confidence 1.0 and up."""
    if canon(lp).split("-")[0] not in OSD_SCRIPT or "osd" not in tesseract_languages(): return {}
    try: r = sh(["tesseract", str(png), "stdout", "--psm", "0", "-l", "osd"], timeout=60, env=tesseract_env())
    except (OSError, subprocess.TimeoutExpired): return {}
    m, c = re.search(r"Script: (\w+)", r.stdout + r.stderr), re.search(r"Script confidence: ([\d.]+)", r.stdout + r.stderr)
    return {"osd_script": m.group(1), "osd_conf": float(c.group(1))} if m and c else {}

def external_ocr(command, png, lp):
    """Run the user's OCR command for a language macOS can't read; {image}, {lang} and {tesseract} are filled in.
    e.g. --ocr-command 'tesseract {image} stdout -l {tesseract}'"""
    lang = canon(lp).split("-")[0]
    tess = tesseract_code(lp)
    try:
        args = [a.format(image=str(png), lang=lang, tesseract=tess,
                         tesseract_with_english=tess if tess == "eng" else f"eng+{tess}") for a in shlex.split(command)]
    except (KeyError, IndexError, ValueError) as e:
        raise Fail(f"unknown placeholder {e} in --ocr-command; use {{image}}, {{lang}}, {{tesseract}}, {{tesseract_with_english}}")
    try:
        r = sh(args, timeout=180, env=tesseract_env())
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Fail(f"--ocr-command failed on {png.name}: {e}")
    if r.returncode != 0:
        hint = f" (install the language data: {install_hint('tesseract-lang') if is_mac() else install_hint()})" if "Failed loading language" in r.stderr else ""
        raise Fail(f"--ocr-command failed on {png.name}: {(r.stderr or r.stdout).strip()[-200:]}{hint}")
    text = "\n".join(l for l in r.stdout.splitlines() if l.strip())
    return {"text": text, "chars": len(text), "lang": None, "langs": {}, "ocr": "external"}

# Scripts text recognition may read, as the language that stands for them in readable_languages(); others (Greek, Hebrew...) can't be proven
SCRIPT_LANG = {"LATIN": "en", "CYRILLIC": "ru", "ARABIC": "ar", "HIRAGANA": "ja", "KATAKANA": "ja", "CJK": "zh", "HANGUL": "ko",
               "THAI": "th", "DEVANAGARI": "hi"}

def ocr_can_read(text):
    """True if macOS text recognition reads every letter of `text` (so not finding it on screen proves something)."""
    for c in text:
        if not c.isalpha(): continue
        lang = SCRIPT_LANG.get(unicodedata.name(c, " ").split()[0])
        if lang is None or (lang not in ("en", "zh") and lang not in readable_languages()): return False
    return True

def content_rules(table, label, lp):
    """The any/all/not lists of one [expect.<screenshot>] table that apply to a screenshot of this language: its own
    lists plus those of every [expect.<screenshot>.<locale>] naming the language (`pt` covers pt-BR). Also the locale keys used."""
    rules, used = {k: list(v) for k, v in table.items() if isinstance(v, list)}, []
    mine = {c for c in (label, lp) if c} | {canon(c) for c in (label, lp) if c}
    for key, sub in table.items():
        if not isinstance(sub, dict) or key in EXPECT_KEYS: continue
        if key in mine or canon(key) in mine or canon(key) in {m.split("-")[0] for m in mine}:
            used.append(key)
            for k, v in sub.items(): rules.setdefault(k, []).extend(v)
    return rules, used

def check_content(rules, screen):
    """(problems, could-not-verify) for one screen's text against any/all/not lists, normalised like judge_screen does.
    The app's own text (iOS .texts.json) is exact. OCR (Android, or no .texts.json) misses things, so a string it can't
    read is never reported as present or absent: only as not verifiable."""
    text = norm(screen.get("text", ""))
    sure = lambda t: screen.get("ocr") == "app" or ocr_can_read(t)
    seen = lambda t: norm(t) in text
    bad, unsure = [], []
    for t in rules.get("all", []):
        if not seen(t): (bad if sure(t) else unsure).append(f'expected "{t}" on screen')
    any_ = rules.get("any", [])
    if any_ and not any(map(seen, any_)):
        (bad if all(map(sure, any_)) else unsure).append("expected one of " + ", ".join(f'"{t}"' for t in any_) + " on screen")
    for t in rules.get("not", []):
        if seen(t): bad.append(f'"{t}" must not be on screen')
        elif not sure(t): unsure.append(f'checked that "{t}" is absent')
    return bad, unsure

LAST_REPORT = None  # check.json of the last check, for --json

def cmd_check(folder, strings=None, app=None, report_dir=None, strings_files=None, ocr_command=None, ipad_rule=True,
              play_folder="phoneScreenshots", expect=None):
    """Check screenshots: each shows its own language's strings, none is a copy of another language,
    and no language is missing a screen. Works on shotfleet's output or any fastlane/plain folder.
    `expect` ([expect.<screenshot>] tables) also requires the texts the developer listed to be on (or off) each screen."""
    folder = Path(folder)
    run_json = folder / "run.json"
    if app:
        app = Path(app).expanduser()
        if app.suffix == ".apk" and not app.is_file(): raise Fail(f"no APK at {app}")
        if app.suffix not in (".apk", ".app"): raise Fail(build_hint(app))
        if app.suffix == ".app" and not (app / "Info.plist").is_file(): raise Fail(f"no app at {app}")
        if (folder / "screenshots").is_dir() and (folder / "metadata/android").is_dir():  # a fastlane folder for both stores
            was, folder = folder, folder / ("metadata/android" if app.suffix == ".apk" else "screenshots")
            print(f"{was} holds iOS and Android screenshots; checking the {'Android' if app.suffix == '.apk' else 'iOS'} ones "
                  f"in {folder}. Run check again with the other build for the rest")
            run_json = folder / "run.json"
        layout_android = any(folder.glob("metadata/android")) or any(next(folder.glob(f"*/images/{k}"), None) for k in PLAY_FOLDERS)
        layout_ios = (folder / "screenshots").is_dir() or folder.name == "screenshots"
        if (layout_android and not layout_ios and app.suffix == ".app") or (layout_ios and not layout_android and app.suffix == ".apk"):
            raise Fail(f"{folder} holds {'Android' if layout_android else 'iOS'} screenshots but --app is "
                       f"{'an iOS app' if app.suffix == '.app' else 'an APK'}")
        framework_hint(app, bool(strings_files))
        strings = load_strings_apk(app) if app.suffix == ".apk" else load_strings(app)
        if not strings: raise Fail(f"{app.name} contains no translations shotfleet can read (no .lproj strings, String Catalogs or resources)")
        strings = {lp: strings[lp] for lp in shipped_locales(strings)}  # not libraries' en-GB/pt-BR/zh-TW strings
    elif strings_files:  # Flutter, React Native, .NET, Unity, exports: translations from source files
        strings = load_strings_files(strings_files)
        strings = {lp: strings[lp] for lp in shipped_locales(strings)}
    elif strings is None and run_json.exists():
        run = json.loads(run_json.read_text())
        src = run["apk"] if run.get("platform") == "android" else run["app"]
        if run.get("strings"):  # Flutter, React Native, ...: the run read translation files, so check reads them too
            strings = config_strings({"strings": run["strings"], "base_locale": run.get("base_locale", "en")}, Path)
        elif not Path(src).exists():
            raise Fail(f"the app this run used is gone ({src}); pass the build with --app")
        else: strings = load_strings_apk(src) if run.get("platform") == "android" else load_strings(Path(src))
    tables = string_tables(strings or {})
    report = Path(report_dir) if report_dir else (folder if run_json.exists() else Path("shotfleet-check"))
    report.mkdir(parents=True, exist_ok=True)
    images = find_screenshots(folder, platform={".app": "ios", ".apk": "android"}.get(Path(app).suffix) if app else None,
                              play_folder=play_folder)
    if not images:
        raise Fail(f"no screenshots found in {folder}. Expected one of: screenshots/<locale>/*.png (fastlane deliver), "
                   "metadata/android/<locale>/images/phoneScreenshots/*.png (supply), or <locale>/*.png (.jpg files count too)")
    if app is not None: android = Path(app).suffix == ".apk"  # the build says which store's rules apply
    elif run_json.exists(): android = json.loads(run_json.read_text()).get("platform") == "android"
    else: android = any(folder.glob("metadata/android")) or any(next(folder.glob(f"*/images/{k}"), None) for k in PLAY_FOLDERS)
    ios_app = app if app is not None and Path(app).suffix == ".app" else \
        (json.loads(run_json.read_text()).get("app") if run_json.exists() else None)
    if Path(folder).resolve() in (d.resolve() for d in device_runs(Path(folder).resolve().parent)):
        ipad_rule = False  # one device of a multi-device run: the iPad set lives next to it (ipad_set_missing checks that)
    ipad = ipad_rule and bool(ios_app) and "2" in plist_value(Path(ios_app) / "Info.plist", "UIDeviceFamily")
    device = json.loads(run_json.read_text()).get("device", "phone") if run_json.exists() else "phone"
    tablet = play_folder != "phoneScreenshots" or ANDROID_DEVICES.get(device, {}).get("folder") not in (None, "phoneScreenshots")
    store_problems, notes = store_rules(images, android, ipad, tablet)
    unmapped = sorted(l for l in images if tables and not app_locale(l, tables))
    problems = [f"{l}: the app has no {l} translation, so this listing shows another language; translate the app into it or remove the listing" for l in unmapped]
    pngs = [(label, png) for label in sorted(images) if label not in unmapped for png in images[label]]
    ocr_command = ocr_command or os.environ.get("SHOTFLEET_OCR")
    user_gave_command = bool(ocr_command)
    use_vision = vision_available()
    ocr = ocr_tool() if use_vision else None
    texts = [usable_text(png, tables) for _, png in pngs]
    fallback = bool(ocr_command or shutil.which("tesseract"))
    if not use_vision and not all(texts):  # Linux and other systems: Tesseract (or --ocr-command) reads every screenshot
        if not fallback:
            raise Fail("reading screenshots needs Tesseract on this system (macOS text recognition is Mac-only): " + install_hint())
        ocr_command = ocr_command or TESSERACT_COMMAND
    elif not all(texts) and not warm_up_ocr(ocr, timeout=90 if fallback else 600):  # no need to wait long with another OCR at hand
        if not fallback:
            raise Fail("macOS text recognition isn't answering (its ANECompilerService is stuck, usually after heavy "
                       "use); restarting the Mac fixes it. Or install Tesseract and shotfleet uses it automatically: "
                       "brew install tesseract tesseract-lang")
        print("macOS text recognition isn't answering (its ANECompilerService is stuck); using "
              + ("your --ocr-command" if ocr_command else "Tesseract") + " instead")
        use_vision, ocr_command = False, ocr_command or TESSERACT_COMMAND
    # ponytail: 4 at a time; 10 parallel first-use requests are the likely trigger of macOS's text-recognition
    # service wedging (seen twice); raise it if that turns out to be unrelated
    with ThreadPoolExecutor(max_workers=4) as ex:  # each OCR is its own process
        def read(t, png):
            nonlocal use_vision
            if t or not use_vision: return t or {}
            try: return read_text(ocr, png)
            except RuntimeError:  # macOS's OCR hung mid-check: the rest goes to Tesseract
                if not ocr_command and not shutil.which("tesseract"): raise
                print("macOS text recognition stopped answering; using " + ("your --ocr-command" if ocr_command else "Tesseract") + " for the rest")
                use_vision = False
                return {}
        ocrs = list(ex.map(lambda i: read(texts[i], pngs[i][1]), range(len(pngs))))
        auto = not user_gave_command and bool(tesseract_languages())  # installed Tesseract reads what macOS can't (84/85 verified)
        if auto: ocr_command = TESSERACT_COMMAND
        if ocr_command:  # scripts macOS can't read (or everything, when macOS's OCR is stuck) go to the other OCR
            def unreadable(label):
                lang = canon(app_locale(label, tables) or label).split("-")[0]
                return LEGACY.get(lang, lang) not in readable_languages() | {"zh"}
            redo = [i for i, (label, png) in enumerate(pngs)
                    if not texts[i] and (not use_vision or unreadable(label))
                    and (not auto or tesseract_code(app_locale(label, tables) or label) in tesseract_languages())]
            def external(i):
                lp = app_locale(pngs[i][0], tables) or pngs[i][0]
                return {**external_ocr(ocr_command, pngs[i][1], lp), **tesseract_script(pngs[i][1], lp)}
            for i, r in zip(redo, ex.map(external, redo)):
                ocrs[i] = {**ocrs[i], **r}
    rows, by_hash, expected_used, unverified = [], {}, set(), 0
    for (label, png), r in zip(pngs, ocrs):
        lp = app_locale(label, tables)
        h = hashlib.sha256(png.read_bytes()).hexdigest()[:12]
        if r.get("chars", 0) >= 40:  # ponytail: short screens (a watch button) can be identical across languages
            by_hash.setdefault(h, []).append((lp or (canon(label).split("-")[0] if not tables else label), f"{label}/{png.name}"))
        got, problem = judge_screen(lp or label, r, tables if lp else {})
        problem = caption_problem(lp or label, r, tables, problem)
        if blank_screenshot(png):
            problem = ("blank: nothing is drawn on it yet. The app paints its first frame after the flow's wait passed; "
                       "wait for text that is on the screen (extendedWaitUntil: visible: \"...\", timeout: 60000) before takeScreenshot")
        if problem: problems.append(f"{label}/{png.name}: {problem}")
        if dialog := system_dialog(r): problems.append(f"{label}/{png.name}: {dialog}")
        if png.stem in (expect or {}):
            rules, used = content_rules(expect[png.stem], label, lp)
            expected_used.update((png.stem, k) for k in used)
            bad, unsure = check_content(rules, r)
            problems += [f"{label}/{png.name}: {m}" for m in bad]
            notes += [f"{label}/{png.name}: could not verify, {m} (text recognition can't read that script)" for m in unsure]
            unverified += len(unsure)
        rows.append({"file": f"{label}/{png.name}", "src": os.path.relpath(png, report), "sha": h, "lang": got,
                     "chars": r.get("chars", 0)})
    unread = sorted({r["file"].split("/")[0] for r in rows if r["lang"] is None})
    if unread:
        who = "macOS can't read the script of" if vision_available() else "Tesseract can't read the script of"
        print(f"{who} {', '.join(unread)}: those screens were only checked for showing another "
              "language, copies and missing screens")
    for h, hits in by_hash.items():
        langs, files = {lp for lp, _ in hits}, [f for _, f in hits]
        if len(langs) > 1:  # en-GB and en-US both showing the app's English is fine
            problems.append(f"identical image in {len(langs)} languages: {', '.join(files)}")
    names = {r["file"].split("/")[1] for r in rows}  # expected set = union across languages
    for label in sorted(set(images) - set(unmapped)):
        have = {p.name for p in images[label]}
        if have != names:
            problems.append(f"{label}: missing {', '.join(sorted(names - have))}")
    for name in sorted(expect or {}):  # an [expect] for a screenshot that doesn't exist would never be checked: a typo
        if name not in {Path(r["file"]).stem for r in rows}:
            import difflib
            near = difflib.get_close_matches(name, sorted({Path(r["file"]).stem for r in rows}), n=1)
            problems.append(f"[expect.{name}] matches no screenshot" + (f"; did you mean [expect.{near[0]}]?" if near else ""))
        notes += [f"[expect.{name}.{k}] matches none of the languages checked" for k, v in expect[name].items()
                  if isinstance(v, dict) and k not in EXPECT_KEYS and (name, k) not in expected_used]
    global LAST_REPORT; LAST_REPORT = report / "check.json"
    problems += store_problems
    (report / "check.json").write_text(json.dumps({"screenshots": rows, "problems": problems, "notes": notes}, indent=1, ensure_ascii=False))
    write_gallery(report, rows, problems)
    print(f"\nchecked {len(rows)} screenshots in {len(images)} languages: {len(problems)} problem(s)")
    if expect: print(f"content: [expect] checked on {len({r['file'] for r in rows if Path(r['file']).stem in expect})} screens, "
                     f"{unverified} expectation(s) could not be verified (see notes)")
    for p in problems: print(f"  - {p}")
    if notes:
        print(f"notes ({len(notes)}, not blocking):")
        for n in notes[:12]: print(f"  - {n}")
        if len(notes) > 12: print(f"  ... {len(notes) - 12} more in {report / 'check.json'}")
    if report != folder: print(f"report: {report / 'index.html'}")
    return 1 if problems else 0

def write_gallery(out, rows, problems):
    """out/index.html: one row per language, one column per screen; flagged screenshots outlined in red."""
    why = {}  # screenshot -> the reasons it was flagged, shown under the cell and as a tooltip
    for p in problems:
        if p.startswith("identical image"):  # "identical image in N languages: a/x.png, b/x.png"
            for f in p.split(":", 1)[1].split(","): why.setdefault(f.strip(), []).append(p.split(":", 1)[0])
        else:
            f, _, reason = p.partition(":"); why.setdefault(f, []).append(reason.strip() or p)
    flagged = set(why)
    def locate(rel):  # relative to the report; an absolute file: URL when the image lives outside it, so moving the report keeps the images
        return (Path(out) / rel).resolve().as_uri() if rel.startswith("..") else rel
    src = {r["file"]: locate(r.get("src", f"raw/{r['file']}")) for r in rows}
    names = sorted({r["file"].split("/")[1] for r in rows})
    locales = sorted({r["file"].split("/")[0] for r in rows})
    cells = []
    for lp in locales:
        tds = []
        for nm in names:
            f = f"{lp}/{nm}"
            if f in src:
                url = html.escape(src[f], quote=True)
                reason = html.escape("; ".join(why.get(f, [])), quote=True)
                note = f'<small>{reason}</small>' if reason else ""
                tds.append(f'<td><a href="{url}"><img src="{url}" loading="lazy" title="{reason}" class="{"bad" if f in flagged else ""}"></a>{note}</td>')
            else:
                tds.append('<td class="missing">missing</td>')
        cells.append(f"<tr><th>{html.escape(lp)}</th>{''.join(tds)}</tr>")
    probs = "".join(f"<li>{html.escape(p)}</li>" for p in problems) or "<li>none</li>"
    (out / "index.html").write_text(f"""<!doctype html><meta charset="utf-8"><title>shotfleet results</title>
<style>body{{font:14px -apple-system,sans-serif;margin:16px;background:#fafafa}}table{{border-collapse:collapse}}
th{{text-align:right;padding-right:8px;vertical-align:middle}}td{{padding:3px}}img{{width:120px;border:3px solid transparent;border-radius:6px}}
img.bad{{border-color:#d33}}small{{display:block;width:120px;color:#a22;font-size:11px;line-height:1.25}}td.missing{{width:120px;height:260px;background:#fee;color:#d33;text-align:center}}</style>
<h1>shotfleet: {len(rows)} screenshots, {len(locales)} languages</h1><h3>Problems ({len(problems)})</h3><ul>{probs}</ul>
<table><tr><th></th>{''.join(f"<th>{html.escape(n)}</th>" for n in names)}</tr>{''.join(cells)}</table>""")

# ---------- doctor / init / export ----------

def latest_release():
    """Newest released version, or None (offline, or no releases yet)."""
    try:
        with urllib.request.urlopen("https://shotfleet.com/download/VERSION", timeout=5) as r:
            return r.read().decode().strip() or None
    except (OSError, ValueError, UnicodeDecodeError):
        return None

def java_major(java):
    try: r = sh([str(java), "-version"], timeout=30)
    except (OSError, subprocess.TimeoutExpired): return 0
    m = re.search(r'version "(\d+)', r.stderr + r.stdout)
    return int(m.group(1)) if m else 0

def find_java():
    """(ok, JAVA_HOME to set or None) for Maestro, which needs Java 17+. Homebrew's openjdk is keg-only, so installing it
    never puts `java` on the PATH: look in the places a JDK really lives instead of telling people to edit their shell."""
    if (cur := os.environ.get("JAVA_HOME")) and java_major(Path(cur) / "bin/java") >= 17: return True, None
    if shutil.which("java") and java_major(shutil.which("java")) >= 17: return True, None
    homes = [str(tools_home() / "jre"), str(tools_home() / "jre/Contents/Home")]  # what `doctor --fix` installs (Linux, macOS layout)
    homes += [sh(["/usr/libexec/java_home", "-v", "17+"], timeout=30).stdout.strip() if Path("/usr/libexec/java_home").exists() else ""]
    homes += [f"/opt/homebrew/opt/openjdk{v}/libexec/openjdk.jdk/Contents/Home" for v in ("", "@21", "@17")]
    homes += [str(Path.home() / ".sdkman/candidates/java/current")] + sorted(glob.glob("/Library/Java/JavaVirtualMachines/*/Contents/Home"))
    homes += sorted(glob.glob("/usr/lib/jvm/*"), reverse=True)  # Linux
    for h in homes:
        if h and java_major(Path(h) / "bin/java") >= 17: return True, h
    return False, None

@functools.cache
def java_env():
    """Environment additions that make Maestro find its Java ({} when the system's already works)."""
    ok, home = find_java()
    return {"JAVA_HOME": home, "PATH": f"{home}/bin:{os.environ.get('PATH', '')}"} if ok and home else {}

DOCTOR_OCR_TIMEOUT_S = 60  # doctor never waits longer than this for text recognition

# Everything shotfleet relies on from Maestro, in one place: tools/maestro-compat.py checks a Maestro against it, so a new version
# can be vetted without a device (it does not replace a real run: MAESTRO_TESTED means a real run happened).
MAESTRO_INTERFACE = {
    "cli": {"maestro": ["--device"],  # maestro --device A,B test ...
            "maestro test": ["--shard-split", "--format", "--output", "--debug-output"]},
    "format_values": ["JUNIT"],  # --format JUNIT
    "class_strings": {  # constants that must still be in the jars (log lines shotfleet parses, variables it sets, flow keys it writes)
        "log": ["Selected device", "using port", "with execution plan", "ExecutionPlan(flowsToRun=", "maestro.log"],
        "env": ["MAESTRO_DRIVER_STARTUP_TIMEOUT", "MAESTRO_CLI_NO_ANALYTICS"],
        "flow": ["launchApp", "clearState", "tapOn", "assertVisible", "takeScreenshot", "waitForAnimationToEnd", "scrollUntilVisible",
                 "repeat", "runScript", "inputText", "extendedWaitUntil", "permissions", "arguments"],
    },
    "nice_to_have": ["MAESTRO_DEVICE_UDID"],  # lets Android [inputs.<locale>] pick a per-device value (README, Limits)
}

MAESTRO_TESTED = ("2.0.10", "2.11.0")  # the Maestros a real fixture e2e passed on (iOS and Android); extend only after a real run

def parse_maestro_version(*outputs):
    """The version in `maestro --version` output (a line like '2.0.10' or 'v2.0.10', maybe after JVM warnings), or None."""
    for text in outputs:
        for line in reversed((text or "").strip().splitlines()):
            if m := re.match(r"\s*(?:maestro\s+)?v?(\d+(?:\.\d+)+)\b", line, re.I): return m.group(1)
    return None

def read_maestro_version(timeout=120):
    """Installed Maestro's version, or None when it can't be read (garbage output, a timeout: it is a JVM app, slow on a busy Mac)."""
    try: r = sh([maestro_cmd() or "maestro", "--version"], timeout=timeout, env={**os.environ, **java_env()})
    except (OSError, subprocess.TimeoutExpired): return None
    return parse_maestro_version(r.stdout, r.stderr)

def maestro_warning(version):
    """One line when this isn't a Maestro shotfleet was tested with; None when it is. Never a reason to stop."""
    tested = ", ".join(MAESTRO_TESTED)
    if version in MAESTRO_TESTED: return None
    if version is None: return f"could not read Maestro's version; shotfleet was tested with Maestro {tested} and it may work with yours"
    return f"Maestro {version} is not the version shotfleet was tested with ({tested}); it may work"

# ---------- doctor --fix: tools shotfleet can fetch itself ----------
# Rules (research/setup-friction.md): never sudo, never edit PATH or shell rc files, never install Xcode. Everything fetched goes into
# one folder (~/.shotfleet, or $SHOTFLEET_HOME), over HTTPS, and is checked against a SHA-256 (Maestro: pinned here; the JRE:
# Adoptium's API) or SHA-1 (Google's own repository manifest for the Android command-line tools) before it is unpacked.

MAESTRO_PIN = {"version": "2.11.0", "size": 314886578,
               "url": "https://github.com/mobile-dev-inc/maestro/releases/download/cli-2.11.0/maestro.zip",
               "sha256": "5384593cb4e7a106489e75a821d157dd43f4e438df6bc308b72e82c685e1283a"}  # newest Maestro; the fixture e2e passed on it (and on 2.0.10)
ADOPTIUM_ASSETS = "https://api.adoptium.net/v3/assets/latest/21/hotspot"  # Temurin 21 (LTS); Maestro needs Java 17 or newer
ANDROID_REPOSITORY = "https://dl.google.com/android/repository/"

def tools_home():
    return Path(os.environ.get("SHOTFLEET_HOME") or Path.home() / ".shotfleet")

def maestro_cmd():
    """The Maestro to run: $SHOTFLEET_MAESTRO (a path), the one `doctor --fix` installed (a path), else "maestro" from the PATH.
    None when there is none."""
    for c in (os.environ.get("SHOTFLEET_MAESTRO"), tools_home() / "maestro/bin/maestro"):
        if c and os.access(c, os.X_OK): return str(c)
    return "maestro" if shutil.which("maestro") else None  # the PATH one stays a bare name, as before

def download(url, dest, sha256=None, sha1=None, label=None):
    """Fetch `url` to `dest` over HTTPS, printing progress, and refuse it unless it matches the checksum. Written to dest.part first,
    so a half download or a wrong file never sits where the real one belongs."""
    dest = Path(dest); dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    h = hashlib.sha256() if sha256 else hashlib.sha1()
    ctx = tls_context()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": f"shotfleet/{VERSION}"}), timeout=60, context=ctx) as r, part.open("wb") as f:
            total, got, shown = int(r.headers.get("Content-Length") or 0), 0, -1
            while chunk := r.read(1 << 20):
                f.write(chunk); h.update(chunk); got += len(chunk)
                if total and got * 10 // total != shown:
                    shown = got * 10 // total
                    print(f"  {label or dest.name}: {shown * 10}% of {total // (1 << 20)} MB", file=sys.stderr, flush=True)
    except (urllib.error.URLError, OSError, ValueError) as e:
        part.unlink(missing_ok=True)
        raise Fail(f"can't download {url}: {getattr(e, 'reason', e)}")
    want = (sha256 or sha1 or "").lower()
    if want and h.hexdigest() != want:
        part.unlink(missing_ok=True)
        raise Fail(f"{label or dest.name} does not match its checksum (got {h.hexdigest()[:16]}..., expected {want[:16]}...); nothing was installed")
    part.replace(dest)
    return dest

def certifi_path():
    try:
        import certifi
        return certifi.where()
    except ImportError: return None

def tls_context():
    """The CA bundle for downloads: the one the user's environment names (SSL_CERT_FILE and friends: corporate proxies re-sign HTTPS
    with their own CA), else certifi's, else the system's."""
    for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        f = os.environ.get(var)
        if f and Path(f).is_file(): return ssl.create_default_context(cafile=f)
    return ssl.create_default_context(cafile=certifi_path()) if certifi_path() else None

def fetch_text(url):
    ctx = tls_context()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": f"shotfleet/{VERSION}"}), timeout=60, context=ctx) as r:
            return r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise Fail(f"can't reach {url}: {getattr(e, 'reason', e)}")

def extract_zip_safely(archive, target):
    """Unzip into `target`, refusing members that would land outside it, and keep the unix permissions the zip stores (zipfile drops them)."""
    target = Path(target).resolve(); target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            out = (target / info.filename).resolve()
            if not out.is_relative_to(target): raise Fail(f"{Path(archive).name} holds a file outside its folder: {info.filename}")
        for info in z.infolist():
            z.extract(info, target)
            mode = info.external_attr >> 16
            if mode and not info.is_dir(): (target / info.filename).chmod(mode & 0o777 | 0o600)

def install_maestro():
    """Maestro, the pinned version, into <tools home>/maestro. Replaces a copy `doctor --fix` installed earlier."""
    home = tools_home(); pin = MAESTRO_PIN
    tmp = home / "downloads"
    zpath = download(pin["url"], tmp / f"maestro-{pin['version']}.zip", sha256=pin["sha256"], label=f"Maestro {pin['version']}")
    stage = home / "maestro.new"; shutil.rmtree(stage, ignore_errors=True)
    extract_zip_safely(zpath, stage)
    top = next((d for d in (stage / "maestro", stage) if (d / "bin/maestro").is_file()), None)  # 2.0.10 and 2.11.0 have a maestro/ folder; be ready for none
    if not top: shutil.rmtree(stage, ignore_errors=True); raise Fail("the Maestro download has no bin/maestro")
    shutil.rmtree(home / "maestro", ignore_errors=True); top.rename(home / "maestro"); shutil.rmtree(stage, ignore_errors=True)  # stage itself when there was no wrapper folder
    zpath.unlink(missing_ok=True)
    return home / "maestro/bin/maestro"

def adoptium_target(system=None, machine=None):
    system, machine = (system or sys.platform), (machine or host_platform.machine()).lower()
    os_name = "mac" if system == "darwin" else "linux" if system.startswith("linux") else None
    arch = "aarch64" if machine in ("arm64", "aarch64") else "x64" if machine in ("x86_64", "amd64") else None
    if not os_name or not arch: raise Fail(f"no Java download for {system} on {machine}; install Java 17 or newer yourself")
    return os_name, arch

def install_jre():
    """A Temurin 21 JRE into <tools home>/jre (found by find_java). The download link and SHA-256 come from Adoptium's API."""
    os_name, arch = adoptium_target()
    assets = json.loads(fetch_text(f"{ADOPTIUM_ASSETS}?architecture={arch}&image_type=jre&os={os_name}"))
    pkg = next((a["binary"]["package"] for a in assets if a.get("binary", {}).get("image_type") == "jre"), None)
    if not pkg or not pkg.get("link") or not pkg.get("checksum"): raise Fail("Adoptium's API listed no Java 21 JRE for this system")
    home = tools_home()
    archive = download(pkg["link"], home / "downloads" / pkg["name"], sha256=pkg["checksum"], label="Java 21 (Temurin JRE)")
    stage = home / "jre.new"; shutil.rmtree(stage, ignore_errors=True); stage.mkdir(parents=True)
    try:
        with tarfile.open(archive) as t:
            for m in t.getmembers():
                if not (stage / m.name).resolve().is_relative_to(stage.resolve()): raise Fail(f"{archive.name} holds a file outside its folder: {m.name}")
            t.extractall(stage, **TAR_SAFE)
    except (tarfile.TarError, EOFError, OSError) as e:
        shutil.rmtree(stage, ignore_errors=True); raise Fail(f"can't unpack {archive.name}: {e}")
    root = next((d for d in sorted(stage.iterdir()) if d.is_dir()), None)
    if not root: raise Fail(f"{archive.name} is empty")
    shutil.rmtree(home / "jre", ignore_errors=True); root.rename(home / "jre"); shutil.rmtree(stage, ignore_errors=True)
    archive.unlink(missing_ok=True)
    java_env.cache_clear()  # the next lookup sees the new JRE
    return home / "jre"

def android_cmdline_archive(xml_text, system=None, machine=None):
    """(url, sha1, size) of Google's 'cmdline-tools;latest' archive for this system, from the repository manifest."""
    system, machine = (system or sys.platform), (machine or host_platform.machine()).lower()
    host = "macosx" if system == "darwin" else "linux" if system.startswith("linux") else None
    arch = "aarch64" if machine in ("arm64", "aarch64") else "x64"
    m = re.search(r'<remotePackage path="cmdline-tools;latest">(.*?)</remotePackage>', xml_text, re.S)
    if not host or not m: raise Fail("Google's repository manifest has no command-line tools for this system")
    for a in re.findall(r"<archive>(.*?)</archive>", m.group(1), re.S):
        if f"<host-os>{host}</host-os>" in a and (host == "linux" or f"<host-arch>{arch}</host-arch>" in a):
            u, c, z = (re.search(rf"<{t}[^>]*>([^<]*)</{t}>", a) for t in ("url", "checksum", "size"))
            if u and c: return ANDROID_REPOSITORY + u.group(1).strip(), c.group(1).strip(), int(z.group(1)) if z else 0
    raise Fail("Google's repository manifest has no command-line tools for this system")

def fix_sdk_root():
    """Where `doctor --fix` puts Android tools: the folder the user named in ANDROID_HOME / ANDROID_SDK_ROOT, else the SDK found,
    else the Android Studio default for this system."""
    for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(var): return clean_path(os.environ[var])
    return SDK

def install_cmdline_tools(sdk=None):
    """Google's Android command-line tools into <sdk>/cmdline-tools/latest (sdkmanager, avdmanager)."""
    sdk = Path(sdk or fix_sdk_root())
    url, sha1, _ = android_cmdline_archive(fetch_text(ANDROID_REPOSITORY + "repository2-3.xml"))
    archive = download(url, tools_home() / "downloads" / Path(url).name, sha1=sha1, label="Android command-line tools")
    stage = tools_home() / "cmdline.new"; shutil.rmtree(stage, ignore_errors=True)
    extract_zip_safely(archive, stage)
    if not (stage / "cmdline-tools/bin/sdkmanager").is_file(): shutil.rmtree(stage, ignore_errors=True); raise Fail("the download has no cmdline-tools/bin/sdkmanager")
    dest = sdk / "cmdline-tools/latest"; shutil.rmtree(dest, ignore_errors=True); dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(stage / "cmdline-tools"), str(dest)); shutil.rmtree(stage, ignore_errors=True)
    archive.unlink(missing_ok=True)
    return dest / "bin/sdkmanager"

def run_sdkmanager(args, stdin=None, timeout=3600, sdk=None):
    sdk = Path(sdk or fix_sdk_root())
    tool = cmdline_tool("sdkmanager", sdk)
    if not tool: raise Fail("sdkmanager is not installed")
    cmd = sdkmanager_invocation(tool, sdk, args)
    r = subprocess.run(cmd, input=stdin, text=True, env={**os.environ, **java_env()}, timeout=timeout)
    if r.returncode: raise Fail(f"sdkmanager {' '.join(args[:2])} failed (exit {r.returncode})")

def sdkmanager_invocation(tool, sdk, args):
    """The command line for sdkmanager arguments. Google's newer command-line tools turned sdkmanager into a shim for their Android CLI, which reports
    usage data to Google unless told `--no-metrics` (sdkmanager itself does not accept that flag, 2026-10-03). shotfleet promises nothing leaves your
    machine except what you ask for, so when the `android` program sits next to sdkmanager, package installs go through `android --no-metrics sdk install`."""
    android = Path(tool).with_name("android")
    if android.is_file() and args and not args[0].startswith("-"):
        return [str(android), "--no-metrics", f"--sdk={sdk}", "sdk", "install", *args]
    return [str(tool), f"--sdk_root={sdk}", *args]

def fix_plan(have_maestro, have_java, android_pkgs, have_sdkmanager, want_android=True):
    """[(what it does, function)] for what is missing. Nothing here runs sudo, edits a shell file or touches Xcode."""
    plan, root = [], fix_sdk_root()
    if not have_maestro:
        plan.append((f"download Maestro {MAESTRO_PIN['version']} ({MAESTRO_PIN['size'] // (1 << 20)} MB, SHA-256 checked) from github.com into {tools_home()}/maestro", install_maestro))
    if not have_java:
        plan.append((f"download a Java 21 runtime (about 50 MB, SHA-256 from Adoptium) from adoptium.net into {tools_home()}/jre", install_jre))
    if want_android and (android_pkgs or not have_sdkmanager):
        if not have_sdkmanager:
            if is_mac() and shutil.which("brew"):
                plan.append(("brew install --cask android-commandlinetools", lambda: run_cmd(["brew", "install", "--cask", "android-commandlinetools"])))
            else:
                plan.append((f"download Google's Android command-line tools (about 170 MB, SHA-1 from Google's manifest) into {root}/cmdline-tools/latest", lambda: install_cmdline_tools(root)))
        plan.append(("accept the Android SDK licences (https://developer.android.com/studio/terms) with sdkmanager --licenses",
                     lambda: run_sdkmanager(["--licenses"], stdin="y\n" * 50, sdk=root)))
        if android_pkgs:
            plan.append((f"sdkmanager {' '.join(android_pkgs)} (the system image is a large download)", lambda: run_sdkmanager(list(android_pkgs), stdin="y\n" * 10, sdk=root)))
    return plan

def run_cmd(cmd):
    if subprocess.run(cmd).returncode: raise Fail(f"{' '.join(cmd)} failed")

def run_fix_plan(plan, yes=False, stdin_is_tty=None):
    """Print the numbered plan, ask once (or take --yes), run the steps in order and stop at the first failure. 0 ok, 1 a step failed,
    2 nothing was run because nobody agreed."""
    if not plan:
        print("nothing to fix that shotfleet can fetch itself"); return 0
    print(f"doctor --fix would do {len(plan)} thing(s), in this order (never sudo; no shell files or PATH touched):")
    for i, (what, _) in enumerate(plan, 1): print(f"  {i}. {what}")
    if not yes:
        tty = sys.stdin.isatty() if stdin_is_tty is None else stdin_is_tty
        if not tty:
            print("not a terminal, so nothing was run; add --yes to run these"); return 2
        if input(f"Run these {len(plan)}? [y/N] ").strip().lower() not in ("y", "yes"):
            print("nothing was run"); return 2
    for i, (what, fn) in enumerate(plan, 1):
        print(f"[{i}/{len(plan)}] {what}", flush=True)
        try: fn()
        except Fail as e:
            print(f"stopped at step {i}: {e}", file=sys.stderr)
            for j, (rest, _) in enumerate(plan[i:], i + 1): print(f"  not done: {j}. {rest}", file=sys.stderr)
            return 1
    print("done; run shotfleet doctor again to see where you stand")
    return 0

def simctl_works():
    """`xcrun simctl help` answers. It can hang for minutes while other sessions load CoreSimulator (seen 2026-10-03), so it is timed."""
    try: return sh(["xcrun", "simctl", "help"], timeout=120).returncode == 0
    except subprocess.TimeoutExpired: return False

def ios_runtimes():
    """Names of the iOS Simulator runtimes Xcode has (['iOS 26.4']), [] when it has none, None when xcrun can't say."""
    try: listed = sh(["xcrun", "simctl", "list", "runtimes", "-j"])
    except OSError: return None
    try: rts = json.loads(listed.stdout)["runtimes"] if listed.returncode == 0 else None
    except (ValueError, KeyError, TypeError): return None
    return None if rts is None else [r.get("name") or r.get("identifier", "iOS") for r in rts if r.get("platform") == "iOS" and r.get("isAvailable")]

def xcode_hint():
    """What to do when `xcrun simctl` does not answer on a Mac. The usual cause is Xcode installed but not selected (xcode-select still
    points at the Command Line Tools, which have no simctl), so name the Xcode that is there instead of saying 'install Xcode'."""
    xcodes = sorted(p for p in glob.glob("/Applications/Xcode*.app") if os.path.isdir(p + "/Contents/Developer"))
    if xcodes: return (f"Xcode is installed but not selected: sudo xcode-select -s {shlex.quote(xcodes[-1])}/Contents/Developer "
                       "(and once: sudo xcodebuild -license accept)")
    return "install Xcode from the App Store, open it once to accept its licence, and let it add an iOS Simulator runtime"

def cmd_doctor(fix=False, yes=False):
    """Check the tools shotfleet drives; print how to fix what's missing. With fix=True, offer to fetch what it can (fix_plan)."""
    have = lambda c: shutil.which(c) is not None
    mac = is_mac()
    has_aapt2 = bool(sorted((SDK / "build-tools").glob("*/aapt2"))) or have("aapt2")
    image, later = find_image(), "(command below)"
    has_adb, has_emulator, has_avdmanager = adb_cmd() != "adb" or have("adb"), (SDK / "emulator/emulator").exists(), bool(cmdline_tool("avdmanager"))
    has_image = bool(image) or (avd_home() / "shotfleet_android.avd").exists()  # an existing AVD needs no image
    has_maestro = maestro_cmd() is not None
    maestro_v = read_maestro_version() if has_maestro else None  # a JVM app: --version can take long on a busy Mac
    maestro_ok = has_maestro and (maestro_v is None or int(maestro_v.split(".")[0]) >= 2)  # unreadable: installed, warned about below
    tested = ", ".join(MAESTRO_TESTED)
    checks = [
        (f"maestro {maestro_v} (tested: {tested})" if maestro_v else f"maestro (version unknown; tested: {tested})" if has_maestro else "maestro", maestro_ok,
         "shotfleet doctor --fix  (or: curl -Ls https://get.maestro.mobile.dev | bash; shotfleet needs Maestro 2.x)", "both"),
        ("java 17+", find_java()[0], ("brew install openjdk@21  (shotfleet finds Homebrew's Java by itself; Maestro needs 17 or newer)"
                                       if mac else "apt install openjdk-21-jre-headless  (Maestro needs Java 17 or newer)"), "both"),
        *([("swiftc (OCR checks)", have("swiftc") or getattr(sys, "frozen", False), "xcode-select --install", "both")] if mac else
          [("tesseract (screenshot checks)", have("tesseract"), install_hint(), "both")]),
        ("xcrun simctl", simctl_works() if have("xcrun") else False,
         xcode_hint() if mac else "iOS simulators exist only on a Mac with Xcode; this system can run Android", "iOS"),
        *([("/dev/kvm (emulator speed)", os.access("/dev/kvm", os.R_OK | os.W_OK),
            "the emulator needs KVM: enable virtualization, then sudo usermod -aG kvm $USER and log in again", "Android")]
          if sys.platform.startswith("linux") and not mac else []),
        ("adb", has_adb, f"sdkmanager platform-tools {later}", "Android"),
        ("emulator", has_emulator, f"sdkmanager emulator {later}", "Android"),
        ("avdmanager", has_avdmanager, f"sdkmanager command-line tools {later}", "Android"),
        ("aapt2", has_aapt2, f"sdkmanager build-tools {later}", "Android"),
        (f"system image {' '.join(image.split(';')[1:3])}" if image else "system image (API 33+)", has_image, f"sdkmanager a system image of API 33 or newer for {ABI} {later}", "Android"),
    ]
    if mac and next(ok for n, ok, _, _ in checks if n == "xcrun simctl") and (runtimes := ios_runtimes()) is not None:
        checks.append((f"iOS Simulator runtime {runtimes[-1]}" if runtimes else "iOS Simulator runtime", bool(runtimes),
                       "xcodebuild -downloadPlatform iOS  (or Xcode > Settings > Components)", "iOS"))
    for name, ok, how, platform in checks:  # not `fix`: that is the --fix flag, and shadowing it made a plain `doctor` run the fix plan
        print(f"{'ok  ' if ok else 'MISSING'} {name:20} ({platform})" + ("" if ok else f"  -> {how}"))
    if has_maestro and (w := maestro_warning(maestro_v)): print(f"note: {w}")
    print(f"Android SDK: {SDK}" + ("" if any((SDK / part).is_dir() for part in SDK_PARTS) else "  (nothing found there; set ANDROID_HOME if it lives elsewhere)"))
    sdkmanager = cmdline_tool("sdkmanager")
    pkgs = [pkg for ok, pkg in ((has_adb, "platform-tools"), (has_emulator, "emulator"), (has_aapt2, "build-tools;36.0.0"),
                                (has_image, DEFAULT_IMAGE), (has_avdmanager or not sdkmanager, "cmdline-tools;latest")) if not ok]
    if pkgs or not has_avdmanager:  # without sdkmanager, Homebrew's command-line tools (installed first) bring avdmanager too
        cmds = sdkmanager_commands(pkgs) if pkgs else sdkmanager_commands([])[:-1]
        print("Android: to install what is missing, run" + (" (the image is a large download)" if DEFAULT_IMAGE in pkgs else "") + ":\n  " + "\n  ".join(cmds))
    if not mac:
        langs = sorted(l for l in tesseract_languages() if l != "osd")
        print(f"{'ok  ' if len(langs) > 1 else 'note:'} text recognition   Tesseract with {len(langs)} language(s)"
              + ("" if len(langs) > 1 else f"; install more language data to verify other languages ({install_hint()})"))
    if mac:
        print(f"...  text recognition   (first use can take a few minutes while macOS prepares it; doctor waits at most {DOCTOR_OCR_TIMEOUT_S} s)", flush=True)
        try:  # a timeout or an empty answer is a busy Mac or the one-time model compile (17 to 188 s measured), not a broken setup
            t0 = time.time(); r = sh([ocr_tool(), "--warmup"], timeout=DOCTOR_OCR_TIMEOUT_S); read = r.stdout.strip()
        except subprocess.TimeoutExpired:
            read, r = None, None
        except (OSError, RuntimeError) as e:
            read, r = None, e
        if r is None or (isinstance(r, subprocess.CompletedProcess) and r.returncode == 0 and not read):
            print("note: text recognition: slow to start (the Mac is busy or this is the first run: it compiles a model once, up to a few minutes); "
                  f"doctor waited {DOCTOR_OCR_TIMEOUT_S} s and went on. `shotfleet check` waits for it")
        elif isinstance(r, Exception):
            print(f"PROBLEM text recognition   can't start ({r}); restarting the Mac usually fixes it")
        elif r.returncode != 0:
            print(f"PROBLEM text recognition   failed: {(r.stderr or r.stdout).strip()[-200:] or 'exit ' + str(r.returncode)}; restarting the Mac usually fixes it")
        elif read == "Ready":
            print(f"ok   text recognition   ready in {time.time() - t0:.0f} s")
        else:
            print(f"note: text recognition read {read!r} instead of 'Ready'; screenshot checks may be unreliable")
    ok_ios = all(ok for _, ok, _, p in checks if p in ("both", "iOS"))
    ok_android = all(ok for _, ok, _, p in checks if p in ("both", "Android"))
    print(f"\niOS: {'ready' if ok_ios else 'not ready'}   Android: {'ready' if ok_android else 'not ready'}")
    vt = lambda v: tuple(int(n) for n in re.findall(r"\d+", v))
    if (latest := latest_release()) and vt(latest) > vt(VERSION):  # a dev build newer than the release says nothing
        print(f"shotfleet {latest} is out (you have {VERSION}): curl -fsSL https://shotfleet.com/install.sh | sh")
    print("next: shotfleet init  (needs a Debug-iphonesimulator .app and/or a debug .apk of your app)" if ok_ios or ok_android
          else "next: fix the MISSING lines above, then run shotfleet doctor again")
    if fix:
        print()
        fix_pkgs = [pk for pk in pkgs if not (pk == "cmdline-tools;latest" and not sdkmanager)]  # sdkmanager can't install itself
        plan = fix_plan(maestro_ok, find_java()[0], fix_pkgs, bool(sdkmanager))
        if mac and not any(ok for n, ok, _, _ in checks if n == "xcrun simctl"):
            print("not fixable here: iOS needs Xcode and an iOS Simulator runtime (App Store, then Xcode > Settings > Components)")
        if not mac and not have("tesseract"):
            print(f"not run (needs sudo): {install_hint()}")
        code = run_fix_plan(plan, yes)
        if code == 1: return 1
        if plan and code == 0: return 0
    return 0 if ok_ios or ok_android else 2

FLOW_TEMPLATE = """# Write this flow in English: shotfleet translates every text selector for each language.
# Tap and assert by the text the user sees, exactly as it appears in your English strings
# ("Next", not "next"); take a screenshot for each store image you want. No appId needed:
# shotfleet uses each build's own id, so this one flow serves iOS and Android.
# Tips (dialogs, collisions, scrolling): see "Tips" in the README. Maestro's commands: maestro.mobile.dev
- launchApp
- waitForAnimationToEnd:
    timeout: 5000
# An app that draws its first frame late (a Flutter debug build, Compose) can give a blank screenshot: wait for text first.
# - extendedWaitUntil:
#     visible: "<a text on your first screen>"
#     timeout: 60000
- takeScreenshot: 01_home
# - tapOn: "Settings"
# - takeScreenshot: 02_settings
"""

def device_build(app):
    """True for an iphoneos build (archives, device runs): it can't be installed on a simulator."""
    return plist_value(Path(app) / "Info.plist", "DTPlatformName") == "iphoneos"

WRONG_BUILD = {
    ".ipa": "an .ipa is a device build. Pass the simulator .app instead (Build/Products/Debug-iphonesimulator/<App>.app)",
    ".aab": "an .aab can't be installed directly. Build an APK instead: ./gradlew assembleDebug",
    ".xcarchive": "pass the simulator .app, not an archive (archives are device builds): Build/Products/Debug-iphonesimulator/<App>.app, from "
                  "xcodebuild -scheme <Scheme> -sdk iphonesimulator -configuration Debug build",
    ".zip": "unzip it first, then pass the .app or .apk inside",
    ".gz": "unpack it first (tar -xzf), then pass the .app inside",
}

ARCHIVES = (".tar.gz", ".tgz", ".tar", ".zip")
# Python 3.12 deprecates extractall() without a filter and 3.14 makes "data" the default: ask for it where it exists (3.11.4+).
TAR_SAFE = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}

def unpack_build(archive, into):
    """EAS (Expo), CI jobs and download pages hand over a simulator build as .tar.gz, .tgz or .zip: unpack it into `into` and
    return the .app or .apk inside. Members that would land outside `into` are refused."""
    archive, into = Path(archive).expanduser().resolve(), Path(into).resolve()
    if not archive.is_file(): raise Fail(f"no such file: {archive}")
    name = archive.name
    for ext in ARCHIVES:
        if name.lower().endswith(ext): name = name[:-len(ext)]; break
    target = into / name
    if target.exists(): shutil.rmtree(target)
    target.mkdir(parents=True)
    try:
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as z:
                for member in z.namelist():
                    if not (target / member).resolve().is_relative_to(target): raise Fail(f"{archive.name} holds a file outside its folder: {member}")
                z.extractall(target)
        else:
            with tarfile.open(archive) as t:
                for member in t.getmembers():
                    if not (target / member.name).resolve().is_relative_to(target) or member.issym() and not (target / member.name).parent.joinpath(member.linkname).resolve().is_relative_to(target):
                        raise Fail(f"{archive.name} holds a file outside its folder: {member.name}")
                t.extractall(target, **TAR_SAFE)
    except (tarfile.TarError, zipfile.BadZipFile, EOFError, OSError) as e:
        raise Fail(f"can't unpack {archive.name}: " + ("it isn't a valid .zip or .tar.gz (download it again)"
                                                         if isinstance(e, (tarfile.ReadError, zipfile.BadZipFile, EOFError)) else str(e)))
    found = [p for pat in ("*.app", "*/*.app", "*.apk", "*/*.apk") for p in sorted(target.glob(pat)) if p.is_dir() == (p.suffix == ".app")]
    if not found: raise Fail(f"{archive.name} holds no .app or .apk (found: {', '.join(sorted(x.name for x in target.iterdir())) or 'nothing'})")
    return found[0]

def build_hint(app):
    app = Path(app)
    if app.suffix.lower() in WRONG_BUILD: return WRONG_BUILD[app.suffix.lower()]
    inside = next((m for pat in ("*.app", "*/*.app", "*/*/*.app", "*/*/*/*.app") if app.is_dir() and (m := sorted(app.glob(pat)))), [])
    if inside: return f"{app.name} is a folder, not an .app; did you mean {inside[0]}?"
    return "pass a simulator .app or an .apk (Build/Products/Debug-iphonesimulator/<App>.app, or ./gradlew assembleDebug)"

def device_build_message(app):
    return (f"{app.name} is a device build; simulators need a simulator build (Debug-iphonesimulator). "
            "Build with: xcodebuild -scheme <Scheme> -sdk iphonesimulator -configuration Debug build")

def not_a_build(path, platform):
    """Why a file or folder that exists is not what [ios] app / [android] apk wants, and what to point at instead."""
    path = Path(path)
    if path.suffix.lower() in ((".apk", ".aab") if platform == "ios" else (".app", ".ipa", ".xcarchive")):
        return f"{path.name} is for the other platform; [{platform}] takes " + ("a simulator .app" if platform == "ios" else "an .apk")
    return build_hint(path) if platform == "ios" or path.suffix.lower() == ".aab" else "build an APK with ./gradlew assembleDebug"

def config_path(target, dest):
    """How the config should spell a path: relative when it's close (same project), else ~/..."""
    target = Path(target).expanduser().resolve()
    rel = os.path.relpath(target, Path(dest).resolve())
    if not rel.startswith("../../.."): return rel
    home = str(Path.home())
    return "~" + str(target)[len(home):] if str(target).startswith(home + "/") else str(target)

def age(t):
    s = time.time() - t
    return "just now" if s < 90 else f"{s / 60:.0f} min ago" if s < 5400 else f"{s / 3600:.0f} h ago" if s < 172800 else f"{s / 86400:.0f} days ago"

def read_plist(path):
    try: return plistlib.loads(Path(path).read_bytes())
    except Exception: return {}  # missing or unreadable (binary, XML or garbage): no answer

def xcode_projects(cwd):
    """Xcode workspaces and projects in cwd and up to two folders below (ios/App/App.xcodeproj; not Pods, node_modules, hidden
    folders), workspaces first."""
    return [p for pat in ("*.xcworkspace", "*.xcodeproj", "*/*.xcworkspace", "*/*.xcodeproj", "*/*/*.xcworkspace", "*/*/*.xcodeproj") for p in Path(cwd).glob(pat)
            if p.parent.suffix != ".xcodeproj" and not any(x.startswith(".") or x in ("Pods", "node_modules") for x in p.relative_to(cwd).parts)]

def scheme_for(project):
    """Name of the shared scheme that launches an .app, read from the files on disk (never from xcodebuild, whose -list
    resolves Swift packages and wrote 2.4 GB into DerivedData); None when the project has no shared scheme."""
    for d in (project / "xcshareddata/xcschemes", project.with_suffix(".xcodeproj") / "xcshareddata/xcschemes"):
        for f in sorted(d.glob("*.xcscheme")):
            try: root = ET.parse(f).getroot()
            except (ET.ParseError, OSError): continue
            if any(r.get("BuildableName", "").endswith(".app") for r in root.iterfind("LaunchAction//BuildableReference")): return f.stem

def derived_apps(cwd, root=None, configs=("Debug",)):
    """Debug simulator builds in Xcode's DerivedData that belong to the project in cwd, newest first: [(mtime, .app, project)].
    A folder belongs when its info.plist WorkspacePath is cwd, below it (two folders deep, not hidden: worktree copies are
    other copies) or above it; a folder without that key matches when its name starts with a project name found here."""
    root, cwd, found = root or Path.home() / "Library/Developer/Xcode/DerivedData", Path(cwd).resolve(), []
    names = {p.stem.replace(" ", "_") for p in xcode_projects(cwd)}
    for d in sorted(root.glob("*")):
        ws = read_plist(d / "info.plist").get("WorkspacePath")
        if ws:
            proj = Path(ws).resolve().parent
            if proj == cwd or cwd in proj.parents: rel = proj.relative_to(cwd)
            elif proj in cwd.parents: rel = Path()
            else: continue
            if len(rel.parts) > 2 or any(x.startswith(".") for x in rel.parts): continue
            label = (rel / Path(ws).name).as_posix()
        elif d.name.rpartition("-")[0] in names: label = d.name
        else: continue
        for config in configs:
            for app in d.glob(f"Build/Products/{config}-iphonesimulator/*.app"):
                if (t := simulator_app_time(app)) is not None: found.append((t, app, label))
    return sorted(found, reverse=True)

def simulator_app_time(app):
    """When this simulator .app was last built, or None when it is not an installable app (a test runner, a device build)."""
    app = Path(app)
    info = read_plist(app / "Info.plist")
    if info.get("CFBundleExecutable") and not info.get("CFBundleIdentifier", "").endswith(".xctrunner") and info.get("DTPlatformName") != "iphoneos":
        parts = (app, app / "Info.plist", app / info["CFBundleExecutable"])  # a rebuild rewrites these, not always the folder
        return max(x.stat().st_mtime for x in parts if x.exists())

def gradle_apks(cwd):
    """Gradle debug APKs in cwd's app/ (or any module folder one or two levels down, as in android/app of a React Native or
    Capacitor project, or cwd itself), newest first: [(mtime, apk)]."""
    cwd = Path(cwd)
    apks = [a for pat in ("build/outputs/apk/**/debug/*.apk", "*/build/outputs/apk/**/debug/*.apk", "*/*/build/outputs/apk/**/debug/*.apk") for a in cwd.glob(pat)
            if not any(x.startswith(".") or x == "androidTest" for x in a.relative_to(cwd).parts)]
    return sorted(((a.stat().st_mtime, a) for a in set(apks)), reverse=True)

def is_watch_apk(apk):
    try: return "android.hardware.type.watch" in sh([aapt2(), "dump", "badging", str(apk)]).stdout
    except (Fail, OSError): return False  # no aapt2: can't tell, so don't drop it

# ---------- project detection: the source folder of a Flutter, React Native, ... app ----------

class Project:
    """What `shotfleet init` learns from a source folder: the framework, where its translation files are, where its
    builds land and the commands that make them."""
    def __init__(self, name, strings=None, apps=(), apks=(), configs=("Debug",), build_ios="", build_android="", notes=()):
        self.name, self.strings, self.apps, self.apks, self.configs = name, strings, apps, apks, configs
        self.build_ios, self.build_android, self.notes = build_ios, build_android, list(notes)

SKIP_DIRS = {"node_modules", "Pods", "build", "bin", "obj", "DerivedData", "Carthage", "vendor", "venv"}

def source_files(cwd, pattern, depth=5):
    """Files under cwd matching a glob such as '*.arb', not in hidden, build or dependency folders, at most `depth` folders down."""
    cwd, out = Path(cwd), []
    for f in cwd.rglob(pattern):
        parts = f.relative_to(cwd).parts
        if len(parts) <= depth and not any(x.startswith(".") or x in SKIP_DIRS for x in parts[:-1]) and f.is_file(): out.append(f)
    return out

def richest_folder_glob(cwd, ext, min_files=1):
    """'<folder>/*.ext' for the folder with the most translation files of that kind, or None."""
    by_dir = {}
    for f in source_files(cwd, f"*{ext}"):
        if locale_from_path(f) not in (None, "base"): by_dir.setdefault(f.parent, []).append(f)
    best = max(by_dir.items(), key=lambda kv: (len(kv[1]), -len(kv[0].parts)), default=None)
    if not best or len(best[1]) < min_files: return None
    return (best[0].relative_to(cwd).as_posix() + "/" if best[0] != Path(cwd) else "") + f"*{ext}"

def first_glob(cwd, candidates, min_files=1):
    """The first of these globs (relative to cwd) that matches files named like languages."""
    for g in candidates:
        files = [f for f in glob.glob(g, root_dir=cwd) if locale_from_path(Path(f)) not in (None, "base")]
        if len(files) >= min_files: return g
    return None

def read_json_file(path):
    try: return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError): return {}

def flutter_arb_glob(cwd):
    """l10n.yaml's arb-dir (flutter gen-l10n's setting), else the folder with the most .arb files."""
    cfg = Path(cwd) / "l10n.yaml"
    if cfg.is_file():
        m = re.search(r"^\s*arb-dir\s*:\s*['\"]?([^'\"#\n]*?)['\"]?\s*(?:#.*)?$", cfg.read_text(errors="replace"), re.M)
        if m and m.group(1).strip():
            g = m.group(1).strip().rstrip("/") + "/*.arb"
            if glob.glob(g, root_dir=cwd): return g
    return richest_folder_glob(cwd, ".arb") or first_glob(cwd, ["lib/l10n/*.arb"])

I18N_JSON = ["src/locales/*/translation.json", "src/translations/*.json", "src/locales/*.json", "src/i18n/locales/*.json",
             "src/i18n/*.json", "src/lang/*.json", "src/assets/i18n/*.json", "locales/*/translation.json", "locales/*/*.json",
             "locales/*.json", "public/locales/*/translation.json", "assets/locales/*.json", "assets/i18n/*.json",
             "assets/translations/*.json", "assets/lang/*.json", "assets/langs/*.json", "app/i18n/*.json", "app/i18n/locales/*.json", "app/locales/*.json", "app/translations/*.json", "translations/*.json",
             "app/i18n/*.ts", "src/i18n/*.ts", "src/i18n/locales/*.ts", "src/locales/*.ts", "src/translations/*.ts", "i18n/*.ts", "locales/*.ts"]  # .ts: Ignite and friends
I18N_PO = ["src/locales/*/messages.po", "src/locale/locales/*/messages.po", "locales/*/messages.po", "locale/*/LC_MESSAGES/*.po"]

def kotlin_multiplatform(cwd):
    """True when a Gradle build under cwd applies the Kotlin Multiplatform plugin: `kotlin("multiplatform")`, the
    `kotlinMultiplatform` alias of a version catalog, or `org.jetbrains.kotlin.multiplatform`. Looks at the Gradle files up to
    three folders down (kotlinconf-app keeps them in app/shared/) and at gradle/libs.versions.toml."""
    files = [f for pat in ("build.gradle.kts", "build.gradle") for f in source_files(cwd, pat, depth=4)]
    files.append(Path(cwd) / "gradle/libs.versions.toml")
    for f in files:
        try:
            if f.is_file() and f.stat().st_size < 1_000_000 and re.search(r"multiplatform", f.read_text(errors="replace"), re.I): return True
        except OSError: continue
    return False

def is_expo(cwd, pkg, deps):
    """An Expo app (its builds come from `expo run`), not a bare React Native app that merely depends on the `expo` package for some native
    modules (Rocket.Chat does). Bare means ios/ and android/ are committed and nothing says Expo: no app.config, no `expo` key in app.json,
    no Expo entry point. A package.json with only the dependency and no native folders is an Expo app that has not been prebuilt."""
    if "expo" not in deps: return False
    if any((cwd / f).is_file() for f in ("app.config.ts", "app.config.js", "app.config.json")): return True
    app_json = read_json_file(cwd / "app.json")
    if isinstance(app_json, dict) and "expo" in app_json: return True
    if isinstance(pkg, dict) and str(pkg.get("main", "")).startswith(("expo/", "expo-router/")): return True
    return not ((cwd / "ios").is_dir() and (cwd / "android").is_dir())

def detect_project(cwd):
    """The Project for the app whose source is in `cwd`, or None for a native Swift/Kotlin app and for anything unrecognised.
    Reads a few small files (pubspec.yaml, package.json, *.csproj, Gradle settings); never builds or runs anything.
    ponytail: the build paths are the frameworks' documented defaults, not checked on every version of each toolchain."""
    cwd = Path(cwd)
    pkg = read_json_file(cwd / "package.json")
    deps = {**pkg.get("devDependencies", {}), **pkg.get("dependencies", {})} if isinstance(pkg, dict) else {}
    pubspec = (cwd / "pubspec.yaml").read_text(errors="replace") if (cwd / "pubspec.yaml").is_file() else ""
    if re.search(r"^\s+sdk:\s*flutter\b", pubspec, re.M) or re.search(r"^flutter:", pubspec, re.M):
        return Project("Flutter", flutter_arb_glob(cwd) or first_glob(cwd, I18N_JSON),
                       apps=("build/ios/iphonesimulator/*.app",),
                       apks=("build/app/outputs/flutter-apk/*.apk", "build/app/outputs/apk/*/*.apk"),
                       build_ios="flutter build ios --simulator --debug", build_android="flutter build apk --debug",  # framework_hint warns about the DEBUG banner
                       notes=["Flutter joins a row's texts (a ListTile's title and detail) into one label for Maestro: tap it as \"Title.*\"; "
                              "and wait for text before the first takeScreenshot (extendedWaitUntil: visible), a debug build draws late"])
    if "@capacitor/core" in deps or any((cwd / f).is_file() for f in ("capacitor.config.ts", "capacitor.config.json", "capacitor.config.js")):
        return Project("Capacitor", first_glob(cwd, I18N_JSON), apks=("android/app/build/outputs/apk/debug/*.apk",),
                       build_ios="npm run build && npx cap sync ios && xcodebuild -project ios/App/App.xcodeproj -scheme App -configuration Debug "
                                 "-sdk iphonesimulator -derivedDataPath ios/build build",
                       build_android="npm run build && npx cap sync android && (cd android && ./gradlew assembleDebug)",
                       apps=("ios/build/Build/Products/Debug-iphonesimulator/*.app",),
                       notes=["web layers that read navigator.language may ignore the language shotfleet sets on iOS; check the first screenshots"])
    if "react-native" in deps or "expo" in deps:
        expo = is_expo(cwd, pkg, deps)
        return Project("Expo" if expo else "React Native", first_glob(cwd, I18N_PO) or first_glob(cwd, I18N_JSON),
                       apps=("ios/build/Build/Products/Release-iphonesimulator/*.app", "build/Build/Products/Release-iphonesimulator/*.app"),
                       apks=("android/app/build/outputs/apk/release/*.apk",), configs=("Release",),
                       build_ios="npx expo run:ios --configuration Release --no-bundler" if expo else
                       "npx react-native run-ios --mode Release --simulator 'iPhone 17 Pro Max'",
                       build_android="npx expo run:android --variant release --no-bundler" if expo else "(cd android && ./gradlew assembleRelease)")
    csproj = [f for f in cwd.glob("*.csproj")] + [f for f in cwd.glob("*/*.csproj")]
    if any(re.search(r"<UseMaui>\s*true", f.read_text(errors="replace"), re.I) for f in csproj if f.stat().st_size < 1_000_000):
        return Project(".NET MAUI", richest_folder_glob(cwd, ".resx"),
                       apps=("bin/Debug/net*-ios/iossimulator-arm64/*.app", "*/bin/Debug/net*-ios/iossimulator-arm64/*.app"),
                       apks=("bin/Debug/net*-android/*-Signed.apk", "*/bin/Debug/net*-android/*-Signed.apk"),
                       build_ios="dotnet build -f net10.0-ios -c Debug -p:RuntimeIdentifier=iossimulator-arm64",
                       build_android="dotnet build -f net10.0-android -c Debug -p:EmbedAssembliesIntoApk=true")
    if (cwd / "ProjectSettings/ProjectVersion.txt").is_file():
        return Project("Unity", None, notes=["Unity draws its own UI, so text selectors rarely work; shotfleet is not built for games"])
    if any((cwd / n).is_file() for n in ("settings.gradle.kts", "settings.gradle")) and kotlin_multiplatform(cwd):
        return Project("Kotlin Multiplatform", None,  # strings are compiled into native resources shotfleet reads from the build
                       notes=["Compose paints its first frame after its text is readable: start the flow with extendedWaitUntil: visible, and "
                              "pause a moment before the first takeScreenshot (a blank screenshot is captured again once, then reported)"])
    return None

def project_builds(cwd, project, derived=None):
    """(ios apps, apks) of this project's own build folders, newest first: [(mtime, path)]."""
    apps = sorted(((t, a) for pat in project.apps for a in Path(cwd).glob(pat) if (t := simulator_app_time(a)) is not None), reverse=True)
    apks = sorted(((a.stat().st_mtime, a) for pat in project.apks for a in Path(cwd).glob(pat)), reverse=True)
    return apps, apks

def find_builds(cwd, derived=None, project=None):
    """The builds `shotfleet init` uses when none are given: the newest simulator .app for this folder's project and the
    newest APK, each announced in one line. A Flutter, React Native, ... project (`project`, from detect_project) is looked for
    where that framework builds, ahead of Xcode's DerivedData and the Gradle folders. Reads folders only: never runs
    xcodebuild, gradle or the framework's tools. Nothing found: Fail with the exact build commands."""
    cwd = Path(cwd).resolve()
    own = bool(project and (project.build_ios or project.build_android))  # the framework has its own build commands and wording
    apps, apks = derived_apps(cwd, derived, project.configs + ("Debug",) if project else ("Debug",)), gradle_apks(cwd)
    if project:
        own_apps, own_apks = project_builds(cwd, project)
        apps = [(t, a, f"the {project.name} build folder") for t, a in own_apps] or apps
        apks = own_apks or apks
    if len(apks) > 1: apks = [a for a in apks if not is_watch_apk(a[1])] or apks  # the Wear app is not the phone app
    projects = xcode_projects(cwd)
    builds = []
    if apps:
        t, app, where = apps[0]
        print(f"iOS: using {app.name} ({app}): {app.parent.name}, built {age(t)}, the newest of {len(apps)} Xcode build(s) of {where}"
              if not own else
              f"iOS: using {app.name} ({app}): {app.parent.name}, built {age(t)}, the newest of {len(apps)} build(s) found in {where}")
        builds.append(str(app))
    if apks:
        t, apk = apks[0]
        print(f"Android: using {apk.relative_to(cwd)}: built {age(t)}, the newest of {len(apks)} " + ("Gradle debug APK(s)" if not own else "APK(s)") + f" under {cwd}")
        builds.append(str(apk))
    ios_cmd = "xcodebuild -scheme <scheme> -sdk iphonesimulator -configuration Debug build"
    if projects:
        proj = projects[0]
        ios_cmd = (f"xcodebuild {'-workspace' if proj.suffix == '.xcworkspace' else '-project'} {shlex.quote(proj.relative_to(cwd).as_posix())} "
                   f"-scheme {shlex.quote(scheme_for(proj) or '<scheme>')} -sdk iphonesimulator -configuration Debug build")
    android_cmd = "./gradlew assembleDebug"
    if project:  # the framework's own build command: a plain xcodebuild or gradlew skips its code generation and bundling
        ios_cmd, android_cmd = project.build_ios or ios_cmd, project.build_android or android_cmd
        if project.name == "Kotlin Multiplatform" and not project.build_ios:
            ios_cmd += " ARCHS=arm64"  # Xcode 27 also asks for x86_64, which the Gradle build does not have: "Architecture Not Configured in Gradle"
    has_gradle = any((cwd / f).is_file() for f in ("gradlew", "android/gradlew"))
    # (what to build, whether it exists) for the platforms this folder has a project for; none recognised and nothing found: both
    kind = f"{project.name} " if own else ""
    ios_what, android_what = (f"{kind}simulator build", f"{kind}APK") if own else ("Debug simulator build", "Gradle debug APK")
    here = [x for x, present in (((ios_cmd, ios_what, bool(apps)), bool(projects) or bool(project and project.build_ios)),
                                 ((android_cmd, android_what, bool(apks)), has_gradle or bool(project and project.build_android))) if present]
    if not builds:
        what = f"no {ios_what} or {android_what} found for" if own else "no Debug simulator build or Gradle debug APK found for"
        raise Fail(f"{what} {cwd}. Build one, then run shotfleet init again:\n  "
                   + "\n  ".join(c for c, _, _ in here or [(ios_cmd, 0, 0), (android_cmd, 0, 0)]))
    for cmd, what, ok in here:
        if not ok: print(f"note: no {what} yet; to make one: {cmd}")
    return builds

def keep_note(config, dest, builds, text):
    """What init says about a config that is already there: that it names the builds just given, or which it names instead."""
    try: doc = tomllib.loads(Path(config).read_text())
    except (OSError, tomllib.TOMLDecodeError): doc = {}
    named = {str((Path(dest) / Path(sec[k]).expanduser()).resolve()) for s, k in (("ios", "app"), ("android", "apk"))
             if isinstance(sec := doc.get(s), dict) and isinstance(sec.get(k), str)}
    new = {str(Path(b).expanduser().resolve()) for b in builds}
    if new <= named: return " (it already points at this build)"
    return (f", which points at {', '.join(sorted(named)) or 'no build'}, not at {', '.join(sorted(new - named))}. "
            f"Edit it, or delete it and run init again. To add the new build, put this in it:\n{text}")

def cmd_init(builds, dest="."):
    """Write shotfleet.toml + flow.yaml for one or more builds: a simulator .app (iOS) and/or an .apk (Android).
    No builds given: use the newest Debug ones found in the current folder (find_builds)."""
    project = detect_project(Path.cwd())  # a Flutter, React Native, ... source folder: its builds, translation files and commands
    builds = [builds] if isinstance(builds, (str, Path)) else builds or find_builds(Path.cwd(), project=project)
    dest = Path(dest)
    builds = [unpack_build(b, dest / ".shotfleet/builds") if str(b).lower().endswith(ARCHIVES) else b for b in builds]
    sections, found, source_strings = [], [], None
    strings_line = ""
    if project and project.strings:  # these frameworks keep translations in source files, not in the build
        rel = project.strings if dest.resolve() == Path.cwd().resolve() else os.path.join(os.path.relpath(Path.cwd(), dest), project.strings)
        try: source_strings = load_strings_files([str(Path.cwd() / project.strings)])
        except Fail: source_strings = None
        if source_strings:
            strings_line = f'\nstrings = {json.dumps(rel)}   # {project.name}: translations are read from these files'
            print(f"{project.name} project: translations from {project.strings} ({len(source_strings)} languages)")
    elif project:
        print(f"{project.name} project" + (": no translation files found; set strings = \"<glob>\" in the config to point at them"
                                           if project.name != "Kotlin Multiplatform" else ""))
    for n in (project.notes if project else ()): print(f"note: {n}")
    suffixes = [Path(b).suffix for b in builds]
    for kind in (".app", ".apk"):
        if suffixes.count(kind) > 1: raise Fail(f"two {kind} builds given; a config holds one app per platform, so run init once per app")
    for build in builds:
        app = Path(build).expanduser().resolve()
        if app.suffix == ".apk":
            if not app.is_file(): raise Fail(f"no APK at {app}")
            m = re.search(r"package: name='([^']+)'", sh([aapt2(), "dump", "badging", str(app)]).stdout)
            if not m: raise Fail(f"{app.name} doesn't look like a valid APK (aapt2 couldn't read its package name)")
            sections.append(f'[android]\napk = {json.dumps(config_path(app, dest), ensure_ascii=False)}{strings_line}\n'
                            '# devices = ["phone", "tablet"]   # Android sets from one flow\n# locales = ["de", "ja"]   # default: every language the app ships')
            found.append((m.group(1), shipped_locales(source_strings or load_strings_apk(app))))
        elif app.suffix == ".app":
            if not (app / "Info.plist").is_file(): raise Fail(f"no simulator app at {app}")
            if device_build(app): raise Fail(device_build_message(app))
            sections.append(f'[ios]\napp = {json.dumps(config_path(app, dest), ensure_ascii=False)}{strings_line}\n'
                            '# device_types = ["iPhone 17 Pro Max", "iPad Pro 13-inch (M5)"]   # iPhone and iPad sets from one flow\n'
                            '# locales = ["de", "ja"]   # default: every language the app ships')
            found.append((plist_value(app / "Info.plist", "CFBundleIdentifier"), shipped_locales(source_strings or load_strings(app))))
        else:
            raise Fail(build_hint(app))
    for build in builds: framework_hint(Path(build).expanduser().resolve(), bool(strings_line), dest)
    dest.mkdir(parents=True, exist_ok=True)
    hook_text = ""
    if project and dest.resolve() == Path.cwd().resolve() and (project.build_ios or project.build_android):  # hooks run in the config's folder
        cmds = {"ios": project.build_ios, "android": project.build_android}
        if cmds["ios"] and cmds["android"]:
            cmd = f'if [ "$SHOTFLEET_PLATFORM" = ios ]; then {cmds["ios"]}; else {cmds["android"]}; fi'
        else: cmd = cmds["ios"] or cmds["android"]
        hook_text = ("\n\n# Build the app before every run, so `shotfleet run` goes from source to screenshots (uncomment):\n"
                     f"# [hooks]\n# before_run = {json.dumps(cmd)}")
    for name, text in (("shotfleet.toml", "\n\n".join(sections) + hook_text + "\n"), ("flow.yaml", FLOW_TEMPLATE)):
        if (dest / name).exists():
            print(f"keeping existing {dest / name}" + (keep_note(dest / name, dest, builds, text) if name.endswith(".toml") else "")); continue
        (dest / name).write_text(text); print(f"wrote {dest / name}")
    for app_id, locales in found: print(f"{app_id}: {len(locales)} languages ({', '.join(locales)})")
    devices = {(True, False): "simulators", (False, True): "emulators"}.get((".app" in suffixes, ".apk" in suffixes), "simulators and emulators")
    print(f"next: edit {dest / 'flow.yaml'}, then try one language (boots {devices}, takes a few minutes):\n"
          f"  shotfleet run {dest / 'shotfleet.toml'} --locales en")
    return 0

NO_XCRUN = "xcrun isn't available: iOS simulators need a Mac with Xcode (App Store). Run shotfleet doctor to see what else is missing"

def latest_ios_runtime():
    try: listed = sh(["xcrun", "simctl", "list", "runtimes", "-j"])
    except OSError: raise Fail(NO_XCRUN)
    if listed.returncode:
        raise Fail(f"xcrun simctl doesn't work ({(listed.stderr.strip().splitlines() or ['no reason given'])[0]}). Install Xcode and open it once, then run shotfleet doctor")
    ios = [r for r in json.loads(listed.stdout or '{"runtimes": []}')["runtimes"] if r.get("platform") == "iOS" and r.get("isAvailable")]
    if not ios: raise Fail("no iOS Simulator runtime is installed. Install one with: xcodebuild -downloadPlatform iOS (or Xcode > Settings > Components)")
    return ios[-1]["identifier"]

# Android language tag -> Google Play listing locale (fastlane supply folder names)

# App Store screenshot sizes per display class (Apple's Screenshot specifications, 2026-10-01, Duo added 2026-10-03; research/store-specs.md).
# iPhone and iPad sizes are portrait; landscape (swapped) is accepted too.
APPLE_SIZES = {
    'iPhone 6.9"': [(1260, 2736), (1290, 2796), (1320, 2868)], 'iPhone 6.5"': [(1284, 2778), (1242, 2688)],
    'iPhone 6.3"': [(1179, 2556), (1206, 2622)], 'iPhone 6.1"': [(1170, 2532), (1125, 2436), (1080, 2340)],
    'iPhone 5.5"': [(1242, 2208)], 'iPhone 4.7"': [(750, 1334)], 'iPhone 4"': [(640, 1096), (640, 1136), (1136, 600)],
    'iPhone 3.5"': [(640, 920), (640, 960), (960, 600)],  # the (1136, 600) and (960, 600) landscape sizes of the old iPhones are not plain rotations; Apple lists them as written
    'iPhone Duo (outer display)': [(1398, 2034)], 'iPhone Duo (inner display)': [(2007, 2853)],  # listed 2026-10-03; ASC upload "later this year"
    'iPad 13"': [(2064, 2752), (2048, 2732)], 'iPad 11"': [(1488, 2266), (1668, 2420), (1668, 2388), (1640, 2360)],
    'iPad 10.5"': [(1668, 2224)], 'iPad 9.7"': [(1536, 2008), (1536, 2048), (768, 1004), (768, 1024), (2048, 1496), (1024, 748)],
    "Apple Watch": [(422, 514), (410, 502), (416, 496), (396, 484), (368, 448), (312, 390)],
    "Mac": [(1280, 800), (1440, 900), (2560, 1600), (2880, 1800)], "Apple TV / Vision Pro": [(1920, 1080), (3840, 2160)],  # 3840x2160 is also the Vision Pro size
}

def apple_class(size):
    for cls, sizes in APPLE_SIZES.items():
        rotate = cls.startswith(("iPhone", "iPad"))
        if size in sizes or rotate and size and (size[1], size[0]) in sizes: return cls
    return None

def image_info(path):
    """((width, height), has_alpha) for a PNG or JPEG; (None, False) if unreadable."""
    data = Path(path).read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        size = (int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big"))
        alpha = data[25] in (4, 6) or b"tRNS" in data[:data.find(b"IDAT")]  # color type with alpha, or a tRNS chunk
        return size, alpha
    if data[:2] == b"\xff\xd8":  # JPEG: size from the first SOFn marker
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF: i += 1; continue
            marker, length = data[i + 1], int.from_bytes(data[i + 2:i + 4], "big")
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                return (int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")), False
            i += 2 + length
    return None, False

def store_rules(images, android, ipad=False, tablet=False):
    """(problems, notes) against the stores' published screenshot rules (research/store-specs.md).
    Problems are what the store rejects; notes are worth knowing but don't block an upload.
    `tablet`: these are Play's 7" or 10" tablet screenshots, which Google wants at 1080 px or more."""
    problems, notes, long_ones, not_eligible, small_tablet, watch = [], [], {}, [], [], []
    for label, pngs in sorted(images.items()):
        info = {p: image_info(p) for p in pngs}
        for p, (size, alpha) in info.items():
            name = f"{label}/{p.name}"
            if size is None: problems.append(f"{name}: not a PNG or JPEG the stores accept"); continue
            if alpha: problems.append(f"{name}: has transparency (an alpha channel); both stores reject it")
            if android:
                if min(size) < 320 or max(size) > 3840:
                    problems.append(f"{name}: {size[0]}x{size[1]} is outside Google Play's 320-3840 px")
                elif max(size) > 2 * min(size):
                    long_ones.setdefault(size, set()).add(label)
                if tablet and min(size) < 1080: small_tablet.append(name)
            elif apple_class(size) is None:
                problems.append(f"{name}: {size[0]}x{size[1]} isn't an App Store screenshot size")
            elif apple_class(size) == "Apple Watch": watch.append((label, size))
        if android:
            phone = [p for p, (size, _) in info.items() if size]
            if len(phone) > 8: problems.append(f"{label}: {len(phone)} phone screenshots; Google Play takes at most 8")
            big = [p for p in phone if min(info[p][0]) >= 1080 and max(info[p][0]) * 9 == min(info[p][0]) * 16]
            if len(big) < 4: not_eligible.append(label)
        else:
            classes = {}
            for p, (size, _) in info.items():
                if c := apple_class(size): classes.setdefault(c, []).append(p)
            for c, ps in classes.items():
                if len(ps) > 10: problems.append(f"{label}: {len(ps)} {c} screenshots; the App Store takes at most 10")
            iphone = [c for c in classes if c.startswith("iPhone")]
            if iphone and not {'iPhone 6.9"', 'iPhone 6.5"'} & set(iphone):
                problems.append(f"{label}: iPhone screenshots need a 6.9\" or 6.5\" set (has {', '.join(sorted(iphone))})")
            if ipad and not any(c == 'iPad 13"' for c in classes):
                problems.append(f"{label}: the app runs on iPad, so the App Store requires 13\" iPad screenshots")
    if watch:  # Apple: "the same screenshot size for Apple Watch consistently across all localizations"
        sizes = sorted(s for _, s in watch); usual = max(sizes, key=sizes.count)
        for label in sorted({l for l, s in watch if s != usual}):
            problems.append(f"{label}: Apple Watch screenshots aren't {usual[0]}x{usual[1]} like the rest; "
                            "the App Store needs one Watch size in every language")
    if small_tablet:
        notes.append(f"{len(small_tablet)} tablet screenshot(s) ({', '.join(small_tablet[:3])}{', ...' if len(small_tablet) > 3 else ''}) "
                     "are under 1080 px on the short side; Google asks tablet screenshots to be 1,080-7,680 px")
    for (w, h), labels in sorted(long_ones.items()):  # one line per size, not one per file
        notes.append(f"{w}x{h} screenshots in {len(labels)} listing(s) are longer than 2:1, which Google's rules say "
                     "isn't allowed (Play has accepted 20:9 phone screenshots in practice)")
    if not_eligible:
        notes.append(f"{len(not_eligible)} listing(s) ({', '.join(not_eligible[:6])}{', ...' if len(not_eligible) > 6 else ''}) "
                     "have fewer than 4 screenshots at 1080px+ in exactly 9:16 or 16:9 (e.g. 1080x1920), so Google Play "
                     "won't consider them for recommendations")
    return problems, notes

def blank_screenshot(path):
    """True if a PNG shows nothing but one flat area between its status bar and its bottom edge: a frame the app has not drawn yet
    (Flutter debug builds and Compose put their text in the accessibility tree before the first paint, so a flow's wait passes).
    Looks at the middle band only and counts its distinct rows: real UI, even a splash with a logo, has dozens; a blank frame has one or
    two. False for anything it cannot read (interlaced, truncated, not a PNG). ponytail: counts raw rows, not colours, so a screen made of
    flat horizontal stripes only would pass as blank; none seen."""
    try:
        data = Path(path).read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n": return False
        w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", data[16:29])
        if interlace or h < 200 or ctype not in (0, 2, 4, 6): return False
        idat, i = [], 8
        while i + 8 <= len(data):
            n, kind = struct.unpack(">I4s", data[i:i + 8])
            if kind == b"IDAT": idat.append(data[i + 8:i + 8 + n])
            i += 12 + n
        raw = zlib.decompress(b"".join(idat))
        row = 1 + (w * {0: 1, 2: 3, 4: 2, 6: 4}[ctype] * depth + 7) // 8
        if len(raw) < row * h: return False
        band = {raw[y * row:(y + 1) * row] for y in range(h * 12 // 100, h * 88 // 100)}
        return len(band) <= 3
    except (struct.error, zlib.error, ValueError, OSError): return False

def blank_note(folder):
    """The flow-failed text for a language whose screenshots include blank frames, or None. A blank frame is the app's first paint coming
    after the flow's wait; the language is captured again once (that heals a one-off, not an app that always paints late: Compose
    on iOS stays blank and is then reported, so the flow has to wait)."""
    blank = [p.name for p in sorted(Path(folder).glob("*.png")) if blank_screenshot(p)]
    return f"blank screenshot(s): {', '.join(blank)} (the app had not drawn its first frame; wait for text on the screen before takeScreenshot)" if blank else None

def png_size(path):
    """(width, height) from a PNG header, or None if it isn't a PNG."""
    head = Path(path).read_bytes()[:24]
    return (int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")) if head[:8] == b"\x89PNG\r\n\x1a\n" else None

def device_runs(out):
    """Sub-folders of a multi-device run (out/<device>/run.json), or [] for a single run."""
    out = Path(out)
    def has_run(d):
        try: return (d / "run.json").exists()
        except OSError: return False  # a folder this user may not read (/tmp/systemd-private-*) is not a run
    try:
        if has_run(out) or not out.is_dir(): return []
        return sorted(d for d in out.iterdir() if has_run(d))
    except OSError: return []

EXPORT_RESULT = {}  # what `export --json` prints: the listings written and the languages skipped

def cmd_export(out, fastlane, name_prefix=""):
    """Copy verified screenshots into fastlane's upload folders (deliver for iOS, supply for Android).
    Locales with a failed check are skipped, so a bad screenshot can't reach a store listing."""
    if subs := device_runs(out):  # iPhone + iPad: both sets go into the same language folders (sizes differ)
        if ipad_set_missing(out):
            raise Fail('the app runs on iPad, so the App Store requires 13" iPad screenshots; add "iPad Pro 13-inch (M5)" to device_types and run again')
        return max(cmd_export(d, fastlane, f"{d.name}_") for d in subs)  # same screen names on every device
    out, fastlane = Path(out), Path(fastlane)
    own = (out / "run.json").is_file()
    if not own and not any(out.glob("*/*.png")):
        raise Fail(f"no shotfleet run in {out}. Run 'shotfleet run <config>' first")
    # ponytail: screenshots made elsewhere (<locale>/*.png: Watch, Mac, Apple TV, Vision Pro) go to the App Store layout
    # only, as PNG; Play folders and JPEGs from other tools need a shotfleet run or a copy by hand
    run = json.loads((out / "run.json").read_text()) if own else {"platform": "ios"}
    shots = out / "raw" if own else out
    android = run.get("platform") == "android"
    if not (out / "check.json").is_file():
        raise Fail(f"{out} hasn't been checked. Run 'shotfleet check {out}{'' if own else f' --report {out}'}' first")
    problems = json.loads((out / "check.json").read_text())["problems"]
    bad = {p.split(":")[0].split("/")[0] for p in problems if not p.startswith("identical")}
    for p in problems:
        if p.startswith("identical"): bad.update(f.strip().split("/")[0] for f in p.split(":", 1)[1].split(","))
    for lp, r in run.get("locales", {}).items():  # failed captures and empty folders never replace a listing
        if not r.get("ok") or not any((shots / lp).glob("*.png")): bad.add(lp)
    store = PLAY if android else APP_STORE
    root = fastlane / "metadata/android" if android else fastlane / "screenshots"
    existing = sorted(d.name for d in root.iterdir() if d.is_dir()) if root.is_dir() else []
    langs = sorted((d.name for d in shots.iterdir() if d.is_dir() and not d.name.startswith(".")), key=lambda l: -len(l))  # pt-PT before pt
    targets = {}  # listing folder -> app locale whose screenshots it gets
    for lp in langs:
        code = store_code(lp, store)
        if code is None:
            print(f"skip {lp}: {'Google Play' if android else 'the App Store'} has no listing in that language"); continue
        folder = next((e for e in existing if canon(e) == canon(code)), code)  # keep your spelling: nb-NO, he-IL
        targets.setdefault(folder, lp)
    for e in existing:  # listings you already have in the same language: en-GB, es-419, pt-PT get en, es, pt
        lp = e not in targets and app_locale(e, set(langs))
        if lp:
            targets[e] = lp; print(f"{e}: no {e} translation in the app, so it gets the {lp} screenshots")
    done = []
    for folder, lp in sorted(targets.items()):
        if lp in bad: print(f"skip {folder}: {lp} failed checks (see {out / 'check.json'})"); continue
        dst = root / folder / "images" / ANDROID_DEVICES[run.get("device", "phone")]["folder"] if android else root / folder
        dst.mkdir(parents=True, exist_ok=True)
        new = sorted((shots / lp).glob("*.png"))
        sizes = {png_size(p) for p in new}
        for old in dst.glob("*.png"):  # replace this device's set; other sizes (iPad, 6.5") in the folder stay
            if png_size(old) in sizes: old.unlink()
        for png in new: shutil.copy2(png, dst / (name_prefix + png.name))
        done.append(folder)
    print(f"exported {len(done)} listings to {fastlane}: {', '.join(done)}")
    EXPORT_RESULT.update(exported=EXPORT_RESULT.get("exported", []) + done, skipped=sorted(bad))
    return 0 if not bad else 1

COMMANDS = ("doctor", "mcp", "skill", "activate", "deactivate", "init", "run", "check", "export")

def cmd_skill(where, project, force):
    """Copy the agent skills that ship with shotfleet into Claude Code's skills folder (~/.claude/skills, or ./.claude/skills with --project)."""
    src = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "skill"
    skills = sorted(p for p in src.glob("*") if (p / "SKILL.md").is_file()) if src.is_dir() else []
    if not skills: raise Fail(f"no skills found next to the program ({src}). Copy skill/ from the shotfleet repo instead")
    dest = Path(where).expanduser() if where else (Path(".claude/skills") if project else Path.home() / ".claude/skills")
    for s in skills:
        target = dest / s.name
        if target.exists() and not force: print(f"kept {target} (already there; --force replaces it)"); continue
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(s, target, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store")); print(f"installed {target}")
    return 0

def main(argv=None):
    import argparse
    args = sys.argv[1:] if argv is None else argv
    if args and not args[0].startswith("-") and args[0] not in COMMANDS and (exe := shutil.which("shotfleet-" + args[0])):
        os.execv(exe, [exe, *args[1:]])  # `shotfleet foo` runs `shotfleet-foo` from the PATH, like git and gh do
    ap = argparse.ArgumentParser(prog="shotfleet", description="Localized App Store and Google Play screenshots from one English Maestro flow.")
    ap.add_argument("--version", action="version", version=f"shotfleet {VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="command")
    p = sub.add_parser("doctor", help="check that Maestro, Xcode and the Android SDK are ready")
    p.add_argument("--fix", action="store_true", help="offer to download what is missing (Maestro, Java, the Android tools); never uses sudo")
    p.add_argument("--yes", action="store_true", help="with --fix: don't ask before running the steps")
    sub.add_parser("mcp", help="run as an MCP server (for Claude, Cursor and other AI agents)")
    p = sub.add_parser("skill", help="install the Claude Code skills for shotfleet")
    p.add_argument("action", choices=("install",)); p.add_argument("--project", action="store_true", help="install into ./.claude/skills instead of ~/.claude/skills")
    p.add_argument("--dir", help="install into this skills folder (for other agents)"); p.add_argument("--force", action="store_true", help="replace skills that are already installed")
    p = sub.add_parser("activate", help="activate your licence on this Mac"); p.add_argument("key")
    sub.add_parser("deactivate", help="remove the licence from this Mac (a Gumroad activation is not given back: email hello@shotfleet.com)")
    p = sub.add_parser("init", help="write a starter config and flow for your app")
    p.add_argument("builds", nargs="*", metavar="build", help="a simulator .app and/or an .apk (both go in one config); "
                   "none: use the newest Debug build found for the project in this folder")
    p.add_argument("--dir", default=".", help="where to write them (default: here)")
    p = sub.add_parser("run", help="capture every language and check the screenshots")
    p.add_argument("config", nargs="?", default="shotfleet.toml", help="the config file (default: ./shotfleet.toml)")
    p.add_argument("--platform", choices=("ios", "android"), help="only this platform when the config has both")
    p.add_argument("--locales", help="only these languages, comma-separated (e.g. de,ja)")
    p.add_argument("--parallel", type=int, help="how many simulators or emulators to use (default: the config's, or 4)")
    p.add_argument("--json", action="store_true", help="print the check report as JSON on stdout (progress goes to stderr)")
    p.add_argument("--no-hooks", action="store_true", help="don't run the [hooks] commands from the config")
    p = sub.add_parser("check", help="check screenshots from shotfleet, fastlane or any tool")
    p.add_argument("out", help="a shotfleet output folder, a fastlane screenshots/metadata folder, or <locale>/ folders")
    p.add_argument("--app", help="simulator .app or .apk whose strings to check against (not needed for shotfleet's own output)")
    p.add_argument("--report", help="where to write check.json and index.html (default: ./shotfleet-check)")
    p.add_argument("--ocr-command", metavar="CMD",
                   help="text recognition for scripts macOS can't read (Greek, Hebrew, Indic...), e.g. "
                        "\"tesseract {image} stdout -l {tesseract}\" (also SHOTFLEET_OCR)")
    p.add_argument("--strings", action="append", metavar="GLOB",
                   help="translation files instead of --app, e.g. 'lib/l10n/*.arb' or 'locales/*/translation.json' "
                        "(.arb .json .xcstrings .strings .xml .xlf .resx .po .properties .csv); repeatable")
    p.add_argument("--content", nargs="?", const="shotfleet.toml", metavar="CONFIG",
                   help="also check the [expect.<screenshot>] texts of this config (default: ./shotfleet.toml) are on screen; put it after the folder")
    p.add_argument("--json", action="store_true", help="print the check report as JSON on stdout (progress goes to stderr)")
    p = sub.add_parser("export", help="copy screenshots that passed into fastlane's folders")
    p.add_argument("out", help="the run's output folder"); p.add_argument("--fastlane", required=True, help="your fastlane folder")
    p.add_argument("--json", action="store_true", help="print the result as JSON on stdout (progress goes to stderr)")
    p.add_argument("--no-hooks", action="store_true", help="don't run the [hooks] commands from the config")
    a = ap.parse_args(argv)
    if a.cmd == "run" and a.locales is not None and not a.locales.strip(","):
        ap.error("--locales is empty; leave it out to run every language")
    if a.cmd == "run" and a.parallel is not None and a.parallel < 1:
        ap.error("--parallel must be 1 or more")
    if getattr(a, "json", False):  # CI: stdout carries only the JSON report
        EXPORT_RESULT.clear()
        with contextlib.redirect_stdout(sys.stderr): code = main_cmd(a)
        print(json.dumps({"exit": code, **(EXPORT_RESULT if a.cmd == "export" else json.loads(LAST_REPORT.read_text()) if LAST_REPORT and LAST_REPORT.is_file() else {})}, ensure_ascii=False))
        return code
    return main_cmd(a)

MCP_TOOLS = [
    {"name": "check", "description": "Check localized App Store / Google Play screenshots: each shows its own language, "
     "no copies across languages, none missing, and the stores' size/count/transparency rules. Works on fastlane "
     "folders (screenshots/<locale>/, metadata/android/<locale>/images/phoneScreenshots/), shotfleet output, or <locale>/ "
     "folders. Returns the report as JSON (problems, notes, screenshots).",
     "inputSchema": {"type": "object", "required": ["folder"], "properties": {
         "folder": {"type": "string", "description": "folder with the screenshots"},
         "app": {"type": "string", "description": "simulator .app or .apk whose strings to check against"},
         "strings": {"type": "array", "items": {"type": "string"}, "description": "translation file globs instead of app"}}}},
    {"name": "doctor", "description": "Check that Maestro, Xcode and the Android SDK are ready for shotfleet.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "run", "description": "Capture screenshots in every language from a shotfleet.toml config, then check them. "
     "Boots simulators or emulators and takes minutes.",
     "inputSchema": {"type": "object", "required": ["config"], "properties": {
         "config": {"type": "string"}, "locales": {"type": "array", "items": {"type": "string"}}}}},
]

def mcp_call(name, args):
    """One tool call -> (text, is_error). Progress output is captured, not sent over the protocol."""
    global LAST_REPORT
    LAST_REPORT = None  # a run that never reached `check` must not return the previous check's report
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            if name == "doctor": code = cmd_doctor()
            elif name == "check":
                folder = Path(args["folder"]).expanduser()
                code = check_any(folder, args.get("app"), args.get("strings"), args.get("ocr_command"))  # report goes to ./shotfleet-check, never into the checked folder
            elif name == "run": apply_free_tier(); code = cmd_run(args["config"], args.get("locales"))
            else: return f"unknown tool {name}", True
    except Exception as e:  # one bad call must not kill the server
        msg = e if isinstance(e, (Fail, RuntimeError, ValueError, OSError, subprocess.TimeoutExpired)) else f"{type(e).__name__}: {e}"
        return f"{msg}\n\n{log.getvalue()[-2000:]}", True
    report = json.loads(LAST_REPORT.read_text()) if name in ("check", "run") and LAST_REPORT else None
    text = json.dumps({"exit": code, **report}, ensure_ascii=False) if report else log.getvalue()
    return text, False

def cmd_mcp():
    """Model Context Protocol server on stdin/stdout (JSON-RPC, one message per line)."""
    def send(msg): sys.__stdout__.write(json.dumps(msg, ensure_ascii=False) + "\n"); sys.__stdout__.flush()
    for line in sys.stdin:
        if not line.strip(): continue
        try: msg = json.loads(line)
        except ValueError: send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}); continue
        mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
        if mid is None: continue  # notifications (initialized, cancelled)
        if method == "initialize":
            result = {"protocolVersion": params.get("protocolVersion", "2025-06-18"), "capabilities": {"tools": {}},
                      "serverInfo": {"name": "shotfleet", "version": VERSION}}
        elif method == "tools/list": result = {"tools": MCP_TOOLS}
        elif method == "tools/call":
            text, err = mcp_call(params.get("name"), params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": text}], "isError": err}
        elif method == "ping": result = {}
        else:
            send({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"unknown method {method}"}}); continue
        send({"jsonrpc": "2.0", "id": mid, "result": result})
    return 0

# ---------- licence (released builds only; a source checkout is the developer's own) ----------

LICENCE_FILE = Path.home() / "Library/Application Support/shotfleet/licence.json"
LICENCE_RECHECK_DAYS, LICENCE_OFFLINE_DAYS = 7, 30
BUY_URL = "https://shotfleet.com/#price"
GUMROAD_API = os.environ.get("SHOTFLEET_GUMROAD_API", "https://api.gumroad.com/v2/licenses")
GUMROAD_PRODUCT_ID = "WxLJHi0WgmVoqCqybcFVPg=="  # set by packaging/go-live.sh
MAX_MACS = 3
FREE_LANGUAGES = 2
LOCALE_CAP = None  # set by `run` without a licence: the free tier captures this many languages

class NoLicence(Fail):
    """No valid licence: `export` stops; `run` falls back to the free tier."""

def cap_locales(locales):
    if LOCALE_CAP is None or len(locales) <= LOCALE_CAP: return locales
    print(f"free tier: capturing {LOCALE_CAP} of {len(locales)} languages ({', '.join(locales[:LOCALE_CAP])}). "
          f"`shotfleet activate <key>` unlocks every language ({BUY_URL})")
    return locales[:LOCALE_CAP]

# The licence calls use tls_context(): certifi's CA bundle (the released build can't count on the Mac's), unless the environment names
# one (SSL_CERT_FILE...), as a corporate proxy that re-signs HTTPS needs.

def is_gumroad_key(key):
    """Gumroad keys are four groups of 8 (ABCDEF12-34567890-...)."""
    return bool(re.fullmatch(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{8}){3}", key.strip()))

def gumroad_verify(key, count_use):
    """Gumroad's licence check -> (ok, uses, reason). Gumroad has no per-Mac activation: `uses` is one counter for the whole key,
    and every check bumps it unless count_use is False. Gumroad answers success:true for a refunded or charged-back purchase
    ("licence enforcement is up to the seller"), so the purchase flags are checked here. A 5xx is an outage, not a verdict."""
    if not GUMROAD_PRODUCT_ID: raise Fail("this build has no Gumroad product id (packaging/go-live.sh sets it)")
    data = urllib.parse.urlencode({"product_id": GUMROAD_PRODUCT_ID, "license_key": key.strip(),
                                   "increment_uses_count": "true" if count_use else "false"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{GUMROAD_API}/verify", data=data), timeout=15, context=tls_context()) as r:
            body = json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:  # an unknown key is a 404 with a JSON message
        with e:
            if e.code >= 500: raise OSError(f"Gumroad answered {e.code}")
            try: body = json.loads(e.read() or b"{}")
            except ValueError: raise OSError(f"Gumroad answered {e.code}")
    except (urllib.error.URLError, TimeoutError) as e:
        raise OSError(f"can't reach the licence server ({getattr(e, 'reason', e)})")
    if not body.get("success"): return False, 0, body.get("message", "invalid key").rstrip(".")
    p = body.get("purchase") or {}
    uses = body.get("uses", 0)
    if p.get("refunded"): return False, uses, "the purchase was refunded"
    if p.get("chargebacked"): return False, uses, "the purchase was charged back"
    if p.get("disputed") and not p.get("dispute_won"): return False, uses, "the purchase is disputed"  # a won dispute keeps the licence
    return True, uses, None

def cmd_activate(key):
    if not is_gumroad_key(key):
        raise Fail("that doesn't look like a shotfleet key (four groups of 8 letters and digits, like ABCDEF12-34567890-ABCDEF12-34567890). "
                   f"Your key is in the Gumroad receipt email: {BUY_URL}")
    # Look first without counting: a refused key, or one with all 3 activations used, must not burn another.
    ok, uses, why = gumroad_verify(key, count_use=False)
    if not ok: raise Fail(f"that key didn't activate: {why}. Your key is in the Gumroad receipt email: {BUY_URL}")
    known = (read_licence() or {}).get("key") == key.strip()  # this Mac already holds it: no new activation
    if not known:
        if uses >= MAX_MACS:
            raise Fail(f"this key has used all {MAX_MACS} activations. Email hello@shotfleet.com and I'll reset the count")
        ok, uses, why = gumroad_verify(key, count_use=True)  # ponytail: two people activating at once can pass 3; I reset by hand
        if not ok: raise Fail(f"that key didn't activate: {why}. Your key is in the Gumroad receipt email: {BUY_URL}")
    LICENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    LICENCE_FILE.write_text(json.dumps({"key": key.strip(), "store": "gumroad", "checked": time.time()}))
    print(f"activated on {socket.gethostname()}. Thanks for buying shotfleet!")
    return 0

def read_licence():
    """The stored licence as a dict, or None when the file is missing or unreadable (a half-written file must never crash a command)."""
    try: lic = json.loads(LICENCE_FILE.read_text())
    except (OSError, ValueError): return None
    if not isinstance(lic, dict) or not lic.get("key"): return None
    checked = lic.get("checked", 0)
    return lic if isinstance(checked, (int, float)) and not isinstance(checked, bool) else None  # a text or null date is as good as a corrupt file

def cmd_deactivate():
    if not LICENCE_FILE.exists(): print("no licence on this Mac"); return 0
    lic = read_licence()
    if lic is None:
        LICENCE_FILE.unlink(); print("the saved licence on this Mac was unreadable, so I removed it. Activate again with: shotfleet activate <key>"); return 0
    LICENCE_FILE.unlink()
    if lic.get("store") == "gumroad":  # freeing an activation takes a Gumroad access token, which can't ship in the program
        print(f"removed from this Mac. Gumroad can't give the activation back from here: "
              f"if all {MAX_MACS} are used, email hello@shotfleet.com and I'll reset the count")
    else:
        print("removed from this Mac (it was a licence from a store shotfleet no longer uses)")
    return 0

def require_licence():
    """`run` and `export` need a licence in released builds; `check`, `doctor` and `init` are free.
    Checked online at most weekly; works offline for 30 days after the last good check."""
    if not getattr(sys, "frozen", False): return  # running from source
    if key := os.environ.get("SHOTFLEET_KEY"):  # CI: no activation slot used
        try:
            valid, why = gumroad_verify(key, count_use=False)[::2] if is_gumroad_key(key) else (False, "not a shotfleet key")
        except OSError: return  # don't fail a build because the licence server is unreachable
        if not valid: raise NoLicence(f"SHOTFLEET_KEY isn't a valid licence ({why or 'invalid'})")
        return
    if not LICENCE_FILE.exists():
        raise NoLicence(f"`export` and every language in `run` need a licence: shotfleet activate <key> (buy one at {BUY_URL}; checkout is on Gumroad). "
                        "`check` is free, and `run` captures up to 2 languages without one.")
    lic = read_licence()
    if lic is None:
        raise NoLicence("the saved licence on this Mac is unreadable: activate again with `shotfleet activate <key>` (the key is in your purchase email). "
                        "`check` is free, and `run` captures up to 2 languages without one.")
    if lic.get("store") != "gumroad":  # a file from a store shotfleet no longer uses (shotfleet is sold through Gumroad only)
        raise NoLicence("the saved licence on this Mac is from a store shotfleet no longer uses: activate your Gumroad key with `shotfleet activate <key>` "
                        "(it is in your purchase email). `check` is free, and `run` captures up to 2 languages without one.")
    age = (time.time() - lic.get("checked", 0)) / 86400
    if age < -1:  # dated in the future: a hand-edited file would otherwise never be rechecked
        raise NoLicence("the saved licence on this Mac has a date in the future: activate again with `shotfleet activate <key>`. "
                        "`check` is free, and `run` captures up to 2 languages without one.")
    if age < LICENCE_RECHECK_DAYS: return
    try:
        valid, why = gumroad_verify(lic["key"], count_use=False)[::2]
    except OSError:
        if age < LICENCE_OFFLINE_DAYS: return
        raise NoLicence("couldn't reach the licence server for 30 days; connect once to keep using every language in `run`")
    if not valid:
        raise NoLicence(f"this licence is no longer valid ({why}). {BUY_URL}")
    LICENCE_FILE.write_text(json.dumps({**lic, "checked": time.time()}))

def export_with_hooks(out, fastlane):
    """`export`, with the config's before_export / after_export hooks (found through run.json) around it."""
    out = Path(out)
    run_json = next((p for p in [out / "run.json", *[d / "run.json" for d in device_runs(out)]] if p.is_file()), None)
    run = json.loads(run_json.read_text()) if run_json else {}
    hooks, config = {}, run.get("config")
    if config and Path(config).is_file():
        try: hooks = tomllib.loads(Path(config).read_text()).get("hooks", {})
        except tomllib.TOMLDecodeError: pass
    env = {"SHOTFLEET_PLATFORM": run.get("platform", ""), "SHOTFLEET_OUT": str(out.resolve()), "SHOTFLEET_FASTLANE": str(Path(fastlane).resolve()),
           "SHOTFLEET_REPORT": str(out.resolve() / "check.json")}
    rc, cmd = run_hook(hooks, "before_export", config or "", env)
    if rc: raise Fail(f"hook before_export failed (exit {rc}): {cmd}")
    code = cmd_export(out, fastlane)
    rc, cmd = run_hook(hooks, "after_export", config or "", {**env, "SHOTFLEET_EXIT": str(code)})
    if rc: print(f"hook after_export failed (exit {rc}): {cmd}", file=sys.stderr)
    return max(code, 1 if rc else 0)

def apply_free_tier():
    """`run` without a valid licence still runs, for two languages (the free tier shows the product)."""
    global LOCALE_CAP
    try: require_licence()
    except NoLicence as e:
        print(f"note: {e}", file=sys.stderr); LOCALE_CAP = FREE_LANGUAGES

def on_sigterm(*_):  # CI cancelling a job: clean up like Ctrl-C
    raise KeyboardInterrupt

def main_cmd(a):
    signal.signal(signal.SIGTERM, on_sigterm)
    try:
        return main_dispatch(a)
    finally:
        shutdown_sims()

def check_any(folder, app=None, strings_files=None, ocr_command=None, report=None, expect=None):
    """`check` on whatever folder it is: a run, a multi-device run, or Play listings (phone and tablet sets each on their own)."""
    if not Path(folder).is_dir(): raise Fail(f"no folder at {folder}")
    if len(kinds := play_folders(folder)) > 1 or kinds[:1] in (["sevenInchScreenshots"], ["tenInchScreenshots"]):
        base, codes = Path(report) if report else Path("shotfleet-check"), []
        for k in kinds:
            print(f"\n== {k}")
            codes.append(cmd_check(folder, app=app, strings_files=strings_files, ocr_command=ocr_command,
                                   report_dir=base / k if len(kinds) > 1 else base, play_folder=k, expect=expect))
        return max(codes)
    if subs := device_runs(folder):
        codes = [cmd_check(d, app=app, strings_files=strings_files, ocr_command=ocr_command, ipad_rule=False,
                           report_dir=Path(report) / d.name if report else None, expect=expect) for d in subs]
        return max(codes + [ipad_set_missing(folder)])
    if not app and not strings_files and not (Path(folder) / "run.json").exists():
        print("no --app given: checking by language detection only, which can misjudge short screens; treat a language problem as "
              "a hint (pass --app to compare with your app's strings)")
    return cmd_check(folder, app=app, report_dir=report, strings_files=strings_files, ocr_command=ocr_command, expect=expect)

def main_dispatch(a):
    try:
        if a.cmd == "doctor": return cmd_doctor(a.fix, a.yes)
        if a.cmd == "mcp": return cmd_mcp()
        if a.cmd == "skill": return cmd_skill(a.dir, a.project, a.force)
        if a.cmd == "init": return cmd_init(a.builds, a.dir)
        global NO_HOOKS
        NO_HOOKS = bool(getattr(a, "no_hooks", False))
        if a.cmd == "export": require_licence()
        if a.cmd == "run":
            apply_free_tier()
            if maestro_cmd():
                ver = read_maestro_version(60)
                if w := maestro_warning(ver): print(f"note: {w}", file=sys.stderr)
        if a.cmd == "activate": return cmd_activate(a.key)
        if a.cmd == "deactivate": return cmd_deactivate()
        if a.cmd == "run": return cmd_run(a.config, [l.strip() for l in a.locales.split(",") if l.strip()] if a.locales else None, a.parallel, a.platform)
        if a.cmd == "check": return check_any(a.out, a.app, a.strings, a.ocr_command, a.report, read_expect(a.content) if a.content else None)
        if a.cmd == "export": return export_with_hooks(a.out, a.fastlane)
    except (Fail, RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as e:  # worded for people; never exit 1
        print(f"shotfleet: {e}", file=sys.stderr); return 2
    except KeyboardInterrupt:
        kill_stale_drivers()
        print("\nshotfleet: stopped.", file=sys.stderr); return 130

if __name__ == "__main__":
    sys.exit(main())
