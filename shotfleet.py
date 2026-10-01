#!/usr/bin/env python3
"""shotfleet: localized store screenshots from one Maestro flow, on parallel simulators/emulators.

usage: shotfleet doctor
       shotfleet init <App.app | app.apk> [dir]
       shotfleet run <config.toml> [--locales de,ja] [--parallel N]
       shotfleet check <folder> [--app App.app|app.apk] [--report dir]
       shotfleet export <out_dir> --fastlane <fastlane_dir>

For each language the app ships, shotfleet rewrites the flow's English text selectors into that
language using the strings compiled into the app, runs every language in parallel, and verifies
every screenshot (shows that language's strings, isn't a copy of another, none missing).
"""
import sys
if sys.version_info < (3, 11):
    print(f"shotfleet needs Python 3.11 or newer; this is {sys.version.split()[0]} ({sys.executable}).\n"
          "Install one with: brew install python", file=sys.stderr)
    sys.exit(2)
import functools, hashlib, json, os, re, shutil, subprocess, time, tomllib
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
        if device_build(app):
            raise Fail(f"{app.name} is a device build; simulators need a simulator build (Debug-iphonesimulator). "
                       "Build with: xcodebuild -scheme <Scheme> -sdk iphonesimulator -configuration Debug build")
        cfg["app"] = str(app)
    else:
        apk = path(cfg["apk"])
        if not apk.is_file():
            raise Fail(f"no APK at {apk}")
        m = re.search(r"package: name='([^']+)'", sh([aapt2(), "dump", "badging", str(apk)]).stdout)
        if m and m.group(1) != cfg["package"]:
            raise Fail(f"package is {cfg['package']} but the APK is {m.group(1)}")
        cfg["apk"] = str(apk)
    if not shutil.which("maestro"):
        raise Fail("Maestro isn't installed. Install it with: curl -Ls https://get.maestro.mobile.dev | bash")
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
    if not found:
        raise Fail(f"aapt2 not found under {SDK}/build-tools. Install Build-Tools in Android Studio's SDK Manager (or set ANDROID_HOME)")
    return str(found[-1])

# ---------- strings ----------

def plist_value(plist, key):
    """A top-level Info.plist value, or "" (PlistBuddy prints its errors on stdout)."""
    if not Path(plist).is_file(): return ""
    r = sh(["/usr/libexec/PlistBuddy", "-c", f"Print {key}", str(plist)])
    return r.stdout.strip() if r.returncode == 0 else ""

def load_strings(res_dir):
    """{lproj: {key: value}} from every *.strings table in the app: its own *.lproj folders, plus those inside
    frameworks, Swift package bundles and an embedded Watch app (keys there are prefixed with their bundle path),
    plus Compose Multiplatform resources (*.cvr)."""
    res_dir, out = Path(res_dir), {}
    for lproj in sorted(res_dir.rglob("*.lproj")):
        if lproj.stem == "Base": continue  # Base.lproj is layout/fallback storage, not a language
        where = lproj.parent.relative_to(res_dir).as_posix()
        for f in sorted(lproj.glob("*.stringsdict")):
            r = sh(["plutil", "-convert", "json", "-o", "-", str(f)])
            if r.returncode == 0:
                table = stringsdict_forms(json.loads(r.stdout))
                if where != ".": table = {f"{where}/{f.stem}:{k}": v for k, v in table.items()}
                out.setdefault(canon_lproj(lproj.stem), {}).update(table)
        for f in sorted(lproj.glob("*.strings")):
            r = sh(["plutil", "-convert", "json", "-o", "-", str(f)])
            if r.returncode == 0:
                table = json.loads(r.stdout)
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
    import base64
    for line in text.splitlines():
        kind, key, value = (line.split("|", 2) + ["", ""])[:3]
        if kind == "string":
            out.setdefault(loc, {})[f"cmp:{key}"] = base64.b64decode(value).decode("utf-8", "replace")
        elif kind == "plurals":  # ponytail: format inferred from compose-resources' writer, not seen in a real app yet
            for item in value.split(","):
                form, _, b64 = item.partition(":")
                if b64: out.setdefault(loc, {})[f"cmp:{key}#{form}"] = base64.b64decode(b64).decode("utf-8", "replace")

LOCALE_QUALIFIER = re.compile(r"^(?:([a-z]{2,3})(?:-r([A-Z]{2}))?|b\+([a-z]{2,3})((?:\+[A-Za-z0-9]+)*))$")

def android_locale(q):
    """aapt2 config qualifier -> BCP-47 tag ('de', 'pt-rBR' -> 'pt-BR', 'b+zh+Hans' -> 'zh-Hans'); None if not a pure locale."""
    m = LOCALE_QUALIFIER.match(q)
    if not m or q in ("car", "en-rXA", "ar-rXB", "en-rXC"): return None  # 'car' is a UI mode; X? are pseudolocales
    if m.group(3): return m.group(3) + m.group(4).replace("+", "-")
    return m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")

def unescape_android(v):
    return v.replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n")

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
        if m := re.match(r"\s*resource 0x[0-9a-f]+ (string|plurals)/(\S+)", line):
            name, kind, loc = m.group(2), m.group(1), None; continue
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
    import zipfile
    if not zipfile.is_zipfile(apk): return out
    with zipfile.ZipFile(apk) as z:  # Compose Multiplatform keeps its strings in assets, not resources.arsc
        for n in z.namelist():
            if n.endswith(".cvr"): add_cvr(out, n, z.read(n).decode("utf-8", "replace"), base)
    return out

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

def translate_flow(flow, base, target):
    """Rewrite English text selectors to the target language. Returns (flow, untranslated selectors, collisions)."""
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
        keys = by_text.get(text)
        if not keys:
            forms = tr_format(text)
            if forms is None:
                missing.append(text); return None
            pattern = "|".join(map(regex_literal, forms))  # any plural form: no per-language plural rules needed
            return yaml_single_quote(pattern if len(forms) == 1 else f"({pattern})")
        cands = sorted({tg.get(k, text) for tg in targets for k in keys})
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
    elif (m := re.match(r"^(\s*path:\s*)['\"]?([^'\"#]+?)['\"]?\s*(?:#.*)?$", line)) and len(lines) > 1 \
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
    store = store_code(lproj, APP_STORE) or lproj  # number/date formats follow the store locale
    locale = {"zh-Hans": "zh_CN", "zh-Hant": "zh_TW"}.get(store, store.replace("-", "_"))
    args = [f'      AppleLanguages: "({lproj})"', f'      AppleLocale: "{locale}"']
    launch = lambda clear: ["- launchApp:"] + (["    clearState: true"] if clear else []) + ["    arguments:"] + args
    header, sep, body = flow.partition("\n---\n")
    if not sep:
        raise ValueError("flow needs an 'appId:' header followed by '---'")
    header = re.sub(r"(?m)^name:.*\n?", "", header).rstrip() + f"\nname: {lproj}"
    out = launch(clear=True)  # fresh state per locale: onboarding runs every time
    started = False  # any step yet besides comments
    for line in body.splitlines():
        if re.match(r"^\s*- launchApp\s*$", line):
            if started: out += launch(clear=False)
            started = True
        elif re.match(r"^\s*- launchApp:", line):
            raise ValueError("launchApp with options isn't supported yet; use a bare '- launchApp'")
        else:
            started = started or bool(re.match(r"^\s*-", line))
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
    by_name = {d["name"]: d for d in existing if d.get("isAvailable") and d.get("deviceTypeIdentifier", device_type) == device_type}
    for d in existing:  # same name, other device type (config changed): replace it, or screenshots get the wrong size
        if d["name"].startswith(prefix + "-") and d["name"] not in by_name:
            sh(["xcrun", "simctl", "delete", d["udid"]])
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
    except BaseException as e:  # timeout, Ctrl-C, SIGTERM: never leave Maestro and its drivers running
        for p in descendants(proc.pid) | {proc.pid}: sh(["kill", "-9", str(p)])
        partial = proc.communicate()[0] or ""
        if isinstance(e, subprocess.TimeoutExpired): e.output = partial
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
    flow = path(cfg["flow"]).read_text().replace("\r\n", "\n")
    base_locale = resolve_base(strings, cfg.get("base_locale", "en"), cfg["app"])
    en = strings[base_locale]
    locales = only or cfg.get("locales") or shipped_locales(strings, base_locale)
    out = path(cfg.get("out", "out")).resolve()
    # stale flows, logs and JUnit files from an earlier run must never be read as this run's results;
    # raw/<locale> is cleared per locale below, so a partial rerun keeps the other languages
    for d in ("flows", "debug"): shutil.rmtree(out / ".work" / d, ignore_errors=True)
    for f in out.glob("junit*.xml"): f.unlink()
    (out / ".work" / "flows").mkdir(parents=True)

    # translate every flow first, so selector problems show up before any simulator boots
    report = {"locales": {}}
    for lp in locales:
        if lp not in strings:
            print(f"skip {lp}: app has no {lp}.lproj"); continue
        text, missing, clash = translate_flow(flow, en, with_fallback(strings, lp))
        for c in clash: print(f"warning {lp}: {c}; anchor that step (below:/above:) if it taps the wrong element")
        shutil.rmtree(out / "raw" / lp, ignore_errors=True); (out / "raw" / lp).mkdir(parents=True)
        (out / ".work" / "flows" / f"{lp}.yaml").write_text(localize_flow(text, lp, out / "raw" / lp))
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
        flows_dir = out / ".work" / "flows" / f"attempt{attempt}"
        flows_dir.mkdir(parents=True)
        for lp in lps: shutil.copy(out / ".work" / "flows" / f"{lp}.yaml", flows_dir)
        k = min(n, len(lps))
        junit = out / f"junit{attempt}.xml"; junit.unlink(missing_ok=True)
        env = {**os.environ, "MAESTRO_DRIVER_STARTUP_TIMEOUT": "240000", "MAESTRO_CLI_NO_ANALYTICS": "1"}  # 4 drivers starting at once are slow
        try:
            r = run_guarded(["maestro", "--device", ",".join(s.udid for s in pool[:k]), "test", str(flows_dir),
                             "--shard-split", str(k), "--format", "JUNIT", "--output", str(junit),
                             "--debug-output", str(out / ".work" / "debug" / f"attempt{attempt}")],
                            env=env, timeout=cfg.get("timeout_s", 600) * -(-len(lps) // k) + 300)
            (out / f"maestro{attempt}.log").write_text(r.stdout + r.stderr)
        except subprocess.TimeoutExpired as e:
            (out / f"maestro{attempt}.log").write_text(e.output or "")
            print(f"maestro timed out (log: {out / f'maestro{attempt}.log'})")
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
        e = Emu(5700); p = start_emu(avd, e.port, read_only=False); pool.append(e)  # killed by the caller if this fails
        wait_booted([e]); time.sleep(20); e.adb("shell", "reboot", "-p", check=False); p.wait(timeout=120)
        pool.remove(e)
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
    first = next((l for l in body.splitlines() if l.strip() and not l.strip().startswith("#")), "")
    out = [] if re.match(r"\s*- launchApp", first) else ["- launchApp"]
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
    flow = path(cfg["flow"]).read_text().replace("\r\n", "\n")
    expected = count_screenshots(flow)
    # stale flows, logs and JUnit files from an earlier run must never be read as this run's results
    for d in ("flows", "tmp", "debug"): shutil.rmtree(out / ".work" / d, ignore_errors=True)
    for f in out.glob("junit*.xml"): f.unlink()
    report = {"locales": {}}
    for lp in locales:
        if lp not in strings: print(f"skip {lp}: app has no {lp} strings"); continue
        _, missing, clash = translate_flow(flow, base, with_fallback(strings, lp))
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
            text, _, _ = translate_flow(flow, base, [with_fallback(strings, lp) for lp in lps])
            fdir = out / ".work" / "flows" / tag; fdir.mkdir(parents=True)
            for j in range(len(lps)):
                (fdir / f"{tag}_f{j}.yaml").write_text(android_flow(text, f"{tag}_f{j}", out / ".work" / "tmp" / tag / f"f{j}"))
            junit, dbg = out / f"junit_{tag}.xml", out / ".work" / "debug" / tag
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
                src = out / ".work" / "tmp" / tag / f"f{j}"
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

TWINS = {"ms": ("id",), "id": ("ms",)}  # language detection can't tell these apart in UI text (measured, tools/langmatrix.py)
LEGACY = {"in": "id", "iw": "he", "ji": "yi", "tl": "fil", "no": "nb"}  # Android's old codes -> what language detection reports

@functools.cache
def readable_languages():
    """Base languages this Mac's text recognition reads (macOS 27: 33 codes, e.g. CJK, Cyrillic, Arabic, Thai, Hindi;
    not Greek, Hebrew, Armenian, Georgian or most Indic and Southeast Asian scripts)."""
    return {c.split("-")[0] for c in json.loads(sh([ocr_tool(), "--langs"]).stdout or "[]")}

# Only scripts no other language shares: Cyrillic/Arabic/Han/Devanagari would let Russian pass as Ukrainian
SCRIPTS = {"ja": "[\u3040-\u30ff]", "ko": "[\uac00-\ud7af]", "th": "[\u0e00-\u0e7f]"}

BIDI = dict.fromkeys(map(ord, "\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\u061c\u200b\ufeff"))

@functools.lru_cache(maxsize=None)
def norm(text):
    """Text as OCR and string tables can both agree on: NFKC (NBSP, full-width), no bidi/zero-width marks,
    native digits (Arabic-Indic, Persian, Devanagari...) as ASCII, no accents (OCR drops Hungarian ő), casefolded
    (Android's all-caps buttons), single spaces."""
    import unicodedata
    t = unicodedata.normalize("NFKD", text.translate(BIDI))
    t = "".join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in t if not unicodedata.combining(c))
    return " ".join(unicodedata.normalize("NFKC", t).casefold().split())

# printf (%d, %1$@, %.1f, %lld), and {name} / {0} placeholders (ICU, Compose, .NET)
SPEC = re.compile(r"%(?:(\d+)\$)?[-+ 0#']*(?:\d+|\*)?(?:\.\d+)?(?:hh|h|ll|l|q|z|t|j|L)?([@dDiuUxXfFeEgGsScCoaAp%])|\{(\w+)\}")
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
        if m.group(1) or m.group(3): name = m.group(1) or m.group(3)
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
        if m.group(1) or m.group(3): name = m.group(1) or m.group(3)
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
        pats = [format_regex(v, lambda piece: re.escape(norm_piece(piece)), named=False) for v in values
                if has_format(v) and len(re.sub(r"[\W\d_]", "", SPEC.sub("", v))) >= 3]  # "%d" alone matches anything
        t.formats = re.compile("^(?:" + "|".join(f"(?:{p})" for p in pats) + ")$") if pats else None
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

def find_screenshots(folder):
    """{folder label: [png, ...]} for the layouts people actually have: shotfleet's own output (raw/<locale>),
    fastlane supply (metadata/android/<locale>/images/phoneScreenshots), fastlane deliver (screenshots/<locale>),
    or plain <locale>/ folders."""
    folder = Path(folder)
    if (folder / "screenshots").is_dir() and (folder / "metadata/android").is_dir():
        raise Fail(f"{folder} has both iOS and Android screenshots; check {folder / 'screenshots'} and "
                   f"{folder / 'metadata/android'} separately (each with its own --app)")
    for pattern in ("raw/*/*", "metadata/android/*/images/phoneScreenshots/*",
                    "*/images/phoneScreenshots/*", "screenshots/*/*", "*/*"):
        found = sorted(p for p in folder.glob(pattern) if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
        if found:
            out = {}
            for png in found:
                label = png.parent.parent.parent.name if png.parent.name == "phoneScreenshots" else png.parent.name
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

def read_text(ocr, png, timeout=120):
    """OCR one image. Vision can hang on an overloaded Mac, so time out and retry once instead of waiting forever."""
    for _ in range(2):
        try:
            return json.loads(sh([ocr, str(png)], timeout=timeout).stdout or "{}")
        except subprocess.TimeoutExpired:
            pass
    raise RuntimeError(f"text recognition hung twice on {png} (is the Mac overloaded?); run check again")

LAST_REPORT = None  # check.json of the last check, for --json

def cmd_check(folder, strings=None, app=None, report_dir=None):
    """Check screenshots: each shows its own language's strings, none is a copy of another language,
    and no language is missing a screen. Works on shotfleet's output or any fastlane/plain folder."""
    folder = Path(folder)
    run_json = folder / "run.json"
    if app:
        app = Path(app).expanduser()
        if app.suffix == ".apk" and not app.is_file(): raise Fail(f"no APK at {app}")
        if app.suffix not in (".apk", ".app"): raise Fail(build_hint(app))
        if app.suffix == ".app" and not (app / "Info.plist").is_file(): raise Fail(f"no app at {app}")
        layout_android = any(folder.glob("metadata/android")) or any(folder.glob("*/images/phoneScreenshots"))
        layout_ios = (folder / "screenshots").is_dir() or folder.name == "screenshots"
        if (layout_android and not layout_ios and app.suffix == ".app") or (layout_ios and not layout_android and app.suffix == ".apk"):
            raise Fail(f"{folder} holds {'Android' if layout_android else 'iOS'} screenshots but --app is "
                       f"{'an iOS app' if app.suffix == '.app' else 'an APK'}")
        strings = load_strings_apk(app) if app.suffix == ".apk" else load_strings(app)
        if not strings: raise Fail(f"{app.name} contains no translations shotfleet can read (no .lproj strings, String Catalogs or resources)")
        strings = {lp: strings[lp] for lp in shipped_locales(strings)}  # not libraries' en-GB/pt-BR/zh-TW strings
    elif strings is None and run_json.exists():
        run = json.loads(run_json.read_text())
        src = run["apk"] if run.get("platform") == "android" else run["app"]
        if not Path(src).exists():
            raise Fail(f"the app this run used is gone ({src}); pass the build with --app")
        strings = load_strings_apk(src) if run.get("platform") == "android" else load_strings(Path(src))
    tables = string_tables(strings or {})
    report = Path(report_dir) if report_dir else (folder if run_json.exists() else Path("shotfleet-check"))
    report.mkdir(parents=True, exist_ok=True)
    images = find_screenshots(folder)
    if not images:
        raise Fail(f"no screenshots found in {folder}. Expected one of: screenshots/<locale>/*.png (fastlane deliver), "
                   "metadata/android/<locale>/images/phoneScreenshots/*.png (supply), or <locale>/*.png")
    unmapped = sorted(l for l in images if tables and not app_locale(l, tables))
    problems = [f"{l}: the app has no {l} translation, so this listing shows another language" for l in unmapped]
    pngs = [(label, png) for label in sorted(images) if label not in unmapped for png in images[label]]
    ocr = ocr_tool()
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:  # each OCR is its own process
        ocrs = list(ex.map(lambda item: read_text(ocr, item[1]), pngs))
    rows, by_hash = [], {}
    for (label, png), r in zip(pngs, ocrs):
        lp = app_locale(label, tables)
        h = hashlib.sha256(png.read_bytes()).hexdigest()[:12]
        if r.get("chars", 0) >= 40:  # ponytail: short screens (a watch button) can be identical across languages
            by_hash.setdefault(h, []).append((lp or (canon(label).split("-")[0] if not tables else label), f"{label}/{png.name}"))
        got, problem = judge_screen(lp or label, r, tables if lp else {})
        if problem: problems.append(f"{label}/{png.name}: {problem}")
        rows.append({"file": f"{label}/{png.name}", "src": os.path.relpath(png, report), "sha": h, "lang": got,
                     "chars": r.get("chars", 0)})
    unread = sorted({r["file"].split("/")[0] for r in rows if r["lang"] is None})
    if unread:
        print(f"macOS can't read the script of {', '.join(unread)}: those screens were only checked for showing another "
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
    global LAST_REPORT; LAST_REPORT = report / "check.json"
    (report / "check.json").write_text(json.dumps({"screenshots": rows, "problems": problems}, indent=1, ensure_ascii=False))
    write_gallery(report, rows, problems)
    print(f"\nchecked {len(rows)} screenshots in {len(images)} languages: {len(problems)} problem(s)")
    for p in problems: print(f"  - {p}")
    if report != folder: print(f"report: {report / 'index.html'}")
    return 1 if problems else 0

def write_gallery(out, rows, problems):
    """out/index.html: one row per language, one column per screen; flagged screenshots outlined in red."""
    import html
    flagged = {p.split(":")[0] for p in problems}
    for p in problems:  # "identical image in N languages: a/x.png, b/x.png"
        if p.startswith("identical image"): flagged.update(f.strip() for f in p.split(":", 1)[1].split(","))
    src = {r["file"]: r.get("src", f"raw/{r['file']}") for r in rows}
    names = sorted({r["file"].split("/")[1] for r in rows})
    locales = sorted({r["file"].split("/")[0] for r in rows})
    cells = []
    for lp in locales:
        tds = []
        for nm in names:
            f = f"{lp}/{nm}"
            if f in src:
                url = html.escape(src[f], quote=True)
                tds.append(f'<td><a href="{url}"><img src="{url}" loading="lazy" class="{"bad" if f in flagged else ""}"></a></td>')
            else:
                tds.append('<td class="missing">missing</td>')
        cells.append(f"<tr><th>{html.escape(lp)}</th>{''.join(tds)}</tr>")
    probs = "".join(f"<li>{html.escape(p)}</li>" for p in problems) or "<li>none</li>"
    (out / "index.html").write_text(f"""<!doctype html><meta charset="utf-8"><title>shotfleet results</title>
<style>body{{font:14px -apple-system,sans-serif;margin:16px;background:#fafafa}}table{{border-collapse:collapse}}
th{{text-align:right;padding-right:8px;vertical-align:middle}}td{{padding:3px}}img{{width:120px;border:3px solid transparent;border-radius:6px}}
img.bad{{border-color:#d33}}td.missing{{width:120px;height:260px;background:#fee;color:#d33;text-align:center}}</style>
<h1>shotfleet: {len(rows)} screenshots, {len(locales)} languages</h1><h3>Problems ({len(problems)})</h3><ul>{probs}</ul>
<table><tr><th></th>{''.join(f"<th>{html.escape(n)}</th>" for n in names)}</tr>{''.join(cells)}</table>""")

# ---------- doctor / init / export ----------

def cmd_doctor():
    """Check the tools shotfleet drives; print how to fix what's missing."""
    have = lambda c: shutil.which(c) is not None
    has_aapt2 = bool(sorted((SDK / "build-tools").glob("*/aapt2")))
    maestro = sh(["maestro", "--version"], timeout=60).stdout.strip().splitlines()[-1:] if have("maestro") else []
    maestro_ok = bool(maestro) and maestro[0].split(".")[0].isdigit() and int(maestro[0].split(".")[0]) >= 2
    checks = [
        (f"maestro {maestro[0] if maestro else ''}".strip(), maestro_ok,
         "curl -Ls https://get.maestro.mobile.dev | bash  (shotfleet needs Maestro 2.x)", "both"),
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
# Tap and assert by the text the user sees, exactly as it appears in your English strings
# ("Next", not "next"); take a screenshot for each store image you want.
# Tips (dialogs, collisions, scrolling): see "Tips" in the README.
- launchApp
- waitForAnimationToEnd:
    timeout: 5000
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
    ".xcarchive": "pass the simulator .app, not an archive (archives are device builds)",
    ".zip": "unzip it first, then pass the .app or .apk inside",
}

def build_hint(app):
    return WRONG_BUILD.get(Path(app).suffix.lower(), "pass a simulator .app or an .apk")

def config_path(target, dest):
    """How the config should spell a path: relative when it's close (same project), else ~/..."""
    target = Path(target).expanduser().resolve()
    rel = os.path.relpath(target, Path(dest).resolve())
    if not rel.startswith("../../.."): return rel
    home = str(Path.home())
    return "~" + str(target)[len(home):] if str(target).startswith(home + "/") else str(target)

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
        cfg = f'[android]\napk = {json.dumps(config_path(app, dest))}\npackage = "{app_id}"\nflow = "flow.yaml"\nparallel = 4\nout = "out"\n'
    elif app.suffix == ".app":
        if not (app / "Info.plist").is_file(): raise Fail(f"no simulator app at {app}")
        if device_build(app): raise Fail(f"{app.name} is a device build: {WRONG_BUILD['.xcarchive']}")
        app_id = sh(["/usr/libexec/PlistBuddy", "-c", "Print CFBundleIdentifier", str(app / "Info.plist")]).stdout.strip()
        locales = shipped_locales(load_strings(app))
        cfg = (f'[ios]\napp = {json.dumps(config_path(app, dest))}\nbundle_id = "{app_id}"\nflow = "flow.yaml"\n'
               'device_type = "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max"   # 1320x2868 = App Store 6.9"\n'
               f'runtime = "{latest_ios_runtime()}"   # newest installed; list them: xcrun simctl list runtimes\n'
               'parallel = 4\nout = "out"\n')
    else:
        raise Fail(build_hint(app))
    for name, text in (("shotfleet.toml", cfg), ("flow.yaml", FLOW_TEMPLATE.format(app_id=app_id))):
        if (dest / name).exists(): print(f"keeping existing {dest / name}"); continue
        (dest / name).write_text(text); print(f"wrote {dest / name}")
    print(f"{app_id}: {len(locales)} languages ({', '.join(locales)})")
    print(f"next: edit {dest / 'flow.yaml'}, then try one language (boots simulators, takes a few minutes):\n"
          f"  shotfleet run {dest / 'shotfleet.toml'} --locales en")
    return 0

def latest_ios_runtime():
    rts = json.loads(sh(["xcrun", "simctl", "list", "runtimes", "-j"]).stdout or '{"runtimes": []}')["runtimes"]
    ios = [r for r in rts if r.get("platform") == "iOS" and r.get("isAvailable")]
    return ios[-1]["identifier"] if ios else "com.apple.CoreSimulator.SimRuntime.iOS-26-5"

# Android language tag -> Google Play listing locale (fastlane supply folder names)

def png_size(path):
    """(width, height) from a PNG header, or None if it isn't a PNG."""
    head = Path(path).read_bytes()[:24]
    return (int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")) if head[:8] == b"\x89PNG\r\n\x1a\n" else None

def cmd_export(out, fastlane):
    """Copy verified screenshots into fastlane's upload folders (deliver for iOS, supply for Android).
    Locales with a failed check are skipped, so a bad screenshot can't reach a store listing."""
    out, fastlane = Path(out), Path(fastlane)
    if not (out / "run.json").is_file():
        raise Fail(f"no shotfleet run in {out}. Run 'shotfleet run <config>' first")
    run = json.loads((out / "run.json").read_text())
    android = run.get("platform") == "android"
    if not (out / "check.json").is_file():
        raise Fail(f"{out} hasn't been checked. Run 'shotfleet check {out}' first")
    problems = json.loads((out / "check.json").read_text())["problems"]
    bad = {p.split(":")[0].split("/")[0] for p in problems if not p.startswith("identical")}
    for p in problems:
        if p.startswith("identical"): bad.update(f.strip().split("/")[0] for f in p.split(":", 1)[1].split(","))
    for lp, r in run.get("locales", {}).items():  # failed captures and empty folders never replace a listing
        if not r.get("ok") or not any((out / "raw" / lp).glob("*.png")): bad.add(lp)
    store = PLAY if android else APP_STORE
    root = fastlane / "metadata/android" if android else fastlane / "screenshots"
    existing = sorted(d.name for d in root.iterdir() if d.is_dir()) if root.is_dir() else []
    langs = sorted((d.name for d in (out / "raw").iterdir() if d.is_dir()), key=lambda l: -len(l))  # pt-PT before pt
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
        dst = root / folder / "images/phoneScreenshots" if android else root / folder
        dst.mkdir(parents=True, exist_ok=True)
        new = sorted((out / "raw" / lp).glob("*.png"))
        sizes = {png_size(p) for p in new}
        for old in dst.glob("*.png"):  # replace this device's set; other sizes (iPad, 6.5") in the folder stay
            if png_size(old) in sizes: old.unlink()
        for png in new: shutil.copy2(png, dst / png.name)
        done.append(folder)
    print(f"exported {len(done)} listings to {fastlane}: {', '.join(done)}")
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
    p.add_argument("--json", action="store_true", help="print the check report as JSON on stdout (progress goes to stderr)")
    p = sub.add_parser("check", help="check screenshots from shotfleet, fastlane or any tool")
    p.add_argument("out", help="a shotfleet output folder, a fastlane screenshots/metadata folder, or <locale>/ folders")
    p.add_argument("--app", help="simulator .app or .apk whose strings to check against (not needed for shotfleet's own output)")
    p.add_argument("--report", help="where to write check.json and index.html (default: ./shotfleet-check)")
    p.add_argument("--json", action="store_true", help="print the check report as JSON on stdout (progress goes to stderr)")
    p = sub.add_parser("export", help="copy screenshots that passed into fastlane's folders")
    p.add_argument("out", help="the run's output folder"); p.add_argument("--fastlane", required=True, help="your fastlane folder")
    a = ap.parse_args(argv)
    if a.cmd == "run" and a.locales is not None and not a.locales.strip(","):
        ap.error("--locales is empty; leave it out to run every language")
    if a.cmd == "run" and a.parallel is not None and a.parallel < 1:
        ap.error("--parallel must be 1 or more")
    if getattr(a, "json", False):  # CI: stdout carries only the JSON report
        import contextlib
        with contextlib.redirect_stdout(sys.stderr): code = main_cmd(a)
        print(json.dumps({"exit": code, **(json.loads(LAST_REPORT.read_text()) if LAST_REPORT else {})}, ensure_ascii=False))
        return code
    return main_cmd(a)

def on_sigterm(*_):  # CI cancelling a job: clean up like Ctrl-C
    raise KeyboardInterrupt

def main_cmd(a):
    import signal
    signal.signal(signal.SIGTERM, on_sigterm)
    try:
        return main_dispatch(a)
    finally:
        for udid in OUR_SIMS: sh(["xcrun", "simctl", "shutdown", udid])  # also clears the status bar override

def main_dispatch(a):
    try:
        if a.cmd == "doctor": return cmd_doctor()
        if a.cmd == "init": return cmd_init(a.app, a.dir)
        if a.cmd == "run": return cmd_run(a.config, [l.strip() for l in a.locales.split(",") if l.strip()] if a.locales else None, a.parallel)
        if a.cmd == "check":
            if not Path(a.out).is_dir(): raise Fail(f"no folder at {a.out}")
            if not a.app and not (Path(a.out) / "run.json").exists():
                print("no --app given: checking by language detection only (pass --app to compare with your app's strings)")
            return cmd_check(a.out, app=a.app, report_dir=a.report)
        if a.cmd == "export": return cmd_export(a.out, a.fastlane)
    except (Fail, RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as e:  # worded for people; never exit 1
        print(f"shotfleet: {e}", file=sys.stderr); return 2
    except KeyboardInterrupt:
        kill_stale_drivers()
        print("\nshotfleet: stopped.", file=sys.stderr); return 130

if __name__ == "__main__":
    sys.exit(main())
