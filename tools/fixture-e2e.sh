#!/bin/sh
# End-to-end test on real simulators and emulators: build the fixture app, then init, doctor, run (iPhone + iPad, de/ja/ar/tr),
# check and export it, and prove the detectors work by planting a copied screenshot and a missing one. Roadmap N7, gate 9.
# The Android half does the same with tools/fixture-app-android on the phone emulator (AVD shotfleet_android), de/ja/ar/tr.
#
#   SHOTFLEET_E2E=1 tools/fixture-e2e.sh [--android] [--platform-only ios|android] [--skip-android] [--keep]
#
# It BOOTS iOS SIMULATORS (shotfleet creates and boots shotfleet-<device>-N and shuts them down again), and with --android also
# EMULATORS (2 read-only copies of shotfleet_android on ports 5702 and 5704), so it refuses to run without SHOTFLEET_E2E=1.
# Run it on a quiet Mac (or Linux box with KVM, Android only): not while another session or run uses them. About 10 minutes for iOS, a few more for Android.
#   (no flag)             only iOS: the default is unchanged
#   --android             iOS, then Android (also SHOTFLEET_E2E_ANDROID=1)
#   --platform-only ios|android   only that platform (android needs no Xcode; ios is the default). On Linux only
#                         `--platform-only android` runs: needs /dev/kvm, 6 GB free memory, Tesseract with deu, jpn, ara and tur data
#   --skip-android        no Android, even with SHOTFLEET_E2E_ANDROID=1
#   --keep                keep the temp work dir (it is also kept when anything fails)
# SHOTFLEET_BIN=/path/to/shotfleet tests a built binary instead of ./shotfleet.py (a built binary needs a licence for the
# export step: activate it, or set SHOTFLEET_KEY). Exit 0 only if every assertion passed.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
KEEP=0; IOS=1; ANDROID=0; [ "${SHOTFLEET_E2E_ANDROID:-}" = 1 ] && ANDROID=1
while [ $# -gt 0 ]; do
  case $1 in
    --keep) KEEP=1 ;;
    --android) ANDROID=1 ;;
    --skip-android) ANDROID=0 ;;
    --platform-only) shift
      case "${1:-}" in ios) IOS=1; ANDROID=0 ;; android) IOS=0; ANDROID=1 ;; *) echo "fixture-e2e: --platform-only takes 'ios' or 'android'" >&2; exit 2 ;; esac ;;
    -h|--help) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "fixture-e2e: unknown option $1 (try --help)" >&2; exit 2 ;;
  esac
  shift
done
if [ "${SHOTFLEET_E2E:-}" != 1 ]; then
  echo "fixture-e2e: refusing to run. This test boots iOS simulators (4 per device type, for about 10 minutes), and with --android" >&2
  echo "emulators too, and must not run while another session uses them. Run it as: SHOTFLEET_E2E=1 $0" >&2
  exit 2
fi
OS=$(uname)
if [ "$OS" != Darwin ]; then  # iOS simulators exist only on a Mac; the Android half also runs on Linux (docs/linux.md, experiment E1)
  [ "$OS" = Linux ] && [ "$ANDROID" = 1 ] && [ "$IOS" = 0 ] || {
    echo "fixture-e2e: on $OS only the Android half runs: $0 --platform-only android (iOS simulators need a Mac)" >&2; exit 2; }
fi

# ---- pre-flight: nothing is created or booted before these pass ----
TMP=${TMPDIR:-/tmp}
free_kb=$(df -Pk "$TMP" | awk 'NR==2{print $4}')
[ "$free_kb" -ge 5242880 ] || { echo "fixture-e2e: only $((free_kb / 1048576)) GB free in $TMP, need 5 GB" >&2; exit 2; }
if [ "$OS" = Darwin ]; then
  free_pct=$(memory_pressure 2>/dev/null | sed -n 's/.*free percentage: *\([0-9]*\)%.*/\1/p' | tail -1)
  level=$(sysctl -n kern.memorystatus_vm_pressure_level 2>/dev/null || echo 1)
  if [ "$level" = 4 ] || [ "${free_pct:-100}" -lt 10 ]; then
    echo "fixture-e2e: memory pressure is critical (level $level, ${free_pct:-?}% free); free memory first" >&2; exit 2
  fi
else  # Linux: two emulators want about 3 GB each, the emulator needs KVM, and check reads de/ja/ar/tr screenshots with Tesseract
  avail_kb=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
  [ "${avail_kb:-0}" -ge 6291456 ] || { echo "fixture-e2e: only $((${avail_kb:-0} / 1048576)) GB of memory available, need 6 GB for two emulators" >&2; exit 2; }
  [ -r /dev/kvm ] && [ -w /dev/kvm ] || { echo "fixture-e2e: /dev/kvm is not usable; without it the emulator is far too slow to mean anything (sudo usermod -aG kvm \$USER, log in again)" >&2; exit 2; }
  command -v tesseract >/dev/null || { echo "fixture-e2e: Tesseract is not installed (apt install tesseract-ocr tesseract-ocr-deu tesseract-ocr-jpn tesseract-ocr-ara tesseract-ocr-tur)" >&2; exit 2; }
  for l in deu jpn ara tur; do
    tesseract --list-langs 2>&1 | grep -qx "$l" || { echo "fixture-e2e: Tesseract has no '$l' data (apt install tesseract-ocr-$l)" >&2; exit 2; }
  done
fi

WORK=$(mktemp -d "$TMP/shotfleet-e2e.XXXXXX"); LOGS=$WORK/logs; PY=$WORK/e2e_assert.py
mkdir -p "$LOGS" "$WORK/proj"
sed -n '/^: <<.__PY__.$/,/^__PY__$/p' "$0" | sed '1d;$d' > "$PY"   # the assertion helper is the end of this file (tests/test_fixture_e2e.py loads it the same way)
PASS=0; FAIL=0; LAST_RC=0; PH=""; PS=0; T0=$(date +%s); SIMS=0; EMUS=0
if [ "$OS" = Darwin ]; then DEFAULT_SDK=$HOME/Library/Android/sdk; else DEFAULT_SDK=$HOME/Android/Sdk; fi
ADB=${SHOTFLEET_E2E_ADB:-${ANDROID_HOME:-$DEFAULT_SDK}/platform-tools/adb}; [ -x "$ADB" ] || ADB=adb

# ponytail: the safety net only shuts down simulators named like our own device types' pools, and only once a run has been
# started; shotfleet itself already shuts its pool down on exit. A second shotfleet run started at the same moment would be hit too.
cleanup() {
  if [ "$SIMS" = 1 ]; then
    for u in $(python3 "$PY" sims 2>/dev/null || true); do xcrun simctl shutdown "$u" >/dev/null 2>&1 || true; done
  fi
  # ponytail: shotfleet kills its emulators itself; this only catches an interrupted run. Pre-flight proved no emulator was on
  # ports 5700-5799 when we started, so whatever is there now is shotfleet's (it uses 5700, 5702, 5704...)
  if [ "$EMUS" = 1 ]; then
    for u in $("$ADB" devices 2>/dev/null | awk '/^emulator-57[0-9][0-9][ \t]/{print $1}'); do "$ADB" -s "$u" emu kill >/dev/null 2>&1 || true; done
  fi
  if [ "$KEEP" = 1 ] || [ "$FAIL" -gt 0 ]; then echo "work dir kept: $WORK"; else rm -rf "$WORK"; fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM

say() { printf '%s\n' "$*"; }
ok() { PASS=$((PASS + 1)); say "PASS $1"; }
bad() { FAIL=$((FAIL + 1)); say "FAIL $1${2:+: $2}"; }
phase() {  # phase NAME: print the time the previous phase took, start timing this one ('' ends the last one)
  now=$(date +%s)
  if [ -n "$PH" ]; then say "     [$PH took $((now - PS)) s]"; fi
  PH=$1; PS=$now
  if [ -n "$PH" ]; then say "== $PH"; fi
}
step() {  # step NAME WANT_EXIT cmd...: run it with its output in logs/NAME.log and assert the exit code
  name=$1; want=$2; shift 2; LAST_RC=0
  "$@" >"$LOGS/$name.log" 2>&1 || LAST_RC=$?
  if [ "$LAST_RC" = "$want" ]; then ok "$name exits $want"
  else bad "$name exits $want" "got $LAST_RC, log $LOGS/$name.log"; tail -n 12 "$LOGS/$name.log" | sed 's/^/     | /'; fi
}
py() {  # py ARGS...: run a helper subcommand; its PASS/FAIL lines count as assertions
  python3 "$PY" "$@" >"$LOGS/py.out" 2>&1 || true
  cat "$LOGS/py.out"
  PASS=$((PASS + $(grep -c '^PASS' "$LOGS/py.out" || true))); FAIL=$((FAIL + $(grep -c '^FAIL' "$LOGS/py.out" || true)))
}
sf() { if [ -n "${SHOTFLEET_BIN:-}" ]; then "$SHOTFLEET_BIN" "$@"; else python3 "$ROOT/shotfleet.py" "$@"; fi; }
finish() {
  phase ""
  total=$(($(date +%s) - T0))
  say "total $((total / 60)) min $((total % 60)) s$([ "$total" -gt 600 ] && echo ' (over the 10 minute target)')"
  if [ "$FAIL" = 0 ] && [ "$PASS" -gt 0 ]; then say "PASS: all $PASS assertions passed"; exit 0; fi
  say "FAIL: $FAIL of $((PASS + FAIL)) assertions failed"; exit 1
}

flow_yaml() {  # the one English flow both platforms run: welcome, tap Next, settings
  cat > "$1/flow.yaml" <<'FLOW'
- launchApp
- waitForAnimationToEnd:
    timeout: 5000
- takeScreenshot: 01_welcome
- tapOn: "Next"
- waitForAnimationToEnd:
    timeout: 5000
- takeScreenshot: 02_settings
FLOW
}
hooks_toml() {  # the [hooks] table of both configs: each event appends a line to hooks.log next to the config
  cat <<'TOML'

[hooks]
before_run = 'echo "before_run locales=$SHOTFLEET_LOCALES" >> hooks.log'
after_run = 'echo "after_run exit=$SHOTFLEET_EXIT problems=$SHOTFLEET_PROBLEMS" >> hooks.log'
before_export = 'echo "before_export" >> hooks.log'
after_export = 'echo "after_export exit=$SHOTFLEET_EXIT" >> hooks.log'
TOML
}

say "work dir: $WORK"
if [ "$OS" = Linux ]; then  # the record for experiment E1: what machine these timings come from
  say "machine: $(uname -srm); $(nproc) cores; $(awk '/^MemTotal:/{printf "%d GB", $2/1048576}' /proc/meminfo); KVM $([ -w /dev/kvm ] && echo usable || echo missing)"
  say "cpu: $(awk -F': ' '/^model name/{print $2; exit}' /proc/cpuinfo)"
fi
[ "$ANDROID" = 1 ] || say "SKIP android: not requested (pass --android or set SHOTFLEET_E2E_ANDROID=1; the fixture is tools/fixture-app-android)"
if [ "$IOS" = 1 ] && [ -n "$(python3 "$PY" sims)" ]; then
  echo "fixture-e2e: a shotfleet simulator is already booted (another run?). Wait for it to finish." >&2; exit 2
fi
if [ "$ANDROID" = 1 ] && "$ADB" devices 2>/dev/null | grep -q '^emulator-57[0-9][0-9][[:space:]]'; then
  echo "fixture-e2e: an emulator is already running on a port shotfleet uses (5700-5799: another run?). Wait for it to finish." >&2; exit 2
fi

if [ "$IOS" = 1 ]; then
phase "build the fixture app"
APP=$WORK/build/FleetFixture.app
step build 0 sh "$ROOT/tools/fixture-app/build.sh" "$WORK/build"
[ "$LAST_RC" = 0 ] || finish
[ -f "$APP/Info.plist" ] && ok "build: $APP has an Info.plist" || { bad "build: no Info.plist in $APP"; finish; }

phase "shotfleet init"
# init's no-argument mode only finds Xcode and Gradle builds, which this swiftc-built fixture is not, so the .app is passed
step init 0 sf init "$APP" --dir "$WORK/proj"
[ "$LAST_RC" = 0 ] || finish
[ -f "$WORK/proj/shotfleet.toml" ] && [ -f "$WORK/proj/flow.yaml" ] && ok "init wrote shotfleet.toml and flow.yaml" || { bad "init wrote no config or flow"; finish; }
APPLINE=$(grep '^app = ' "$WORK/proj/shotfleet.toml" || true)
[ -n "$APPLINE" ] || { bad "init's config has no app line"; finish; }
{ printf '[ios]\n%s\n' "$APPLINE"; cat <<'TOML'
device_types = ["iPhone 17 Pro Max", "iPad Pro 13-inch (M5)"]
locales = ["de", "ja", "ar", "tr"]
TOML
hooks_toml; } > "$WORK/proj/shotfleet.toml.new" && mv "$WORK/proj/shotfleet.toml.new" "$WORK/proj/shotfleet.toml"
flow_yaml "$WORK/proj"

phase "shotfleet doctor"
step doctor 0 sf doctor
grep -q 'iOS: ready' "$LOGS/doctor.log" && ok "doctor says iOS: ready" || bad "doctor says iOS: ready" "see $LOGS/doctor.log"

phase "shotfleet run (iPhone, then iPad)"
SIMS=1
step run 0 sf run "$WORK/proj/shotfleet.toml" --locales de,ja,ar,tr
OUT=$WORK/proj/out

phase "shotfleet check"
step check 0 sf check "$OUT"

phase "shotfleet export --fastlane"
step export 0 sf export "$OUT" --fastlane "$WORK/fastlane"

phase "assertions on the output"
py tree --platform ios --out "$OUT" --fastlane "$WORK/fastlane" --hooks "$WORK/proj/hooks.log" --locales de,ja,ar,tr --repo "$ROOT"

phase "planted failures (copies of the output, the real output is untouched)"
for what in copy delete; do
  mkdir -p "$WORK/plant-$what"; cp -R "$OUT" "$WORK/plant-$what/out"; rm -rf "$WORK/plant-$what/out/.work"
  py "plant-$what" "$WORK/plant-$what/out"
  step "check-$what" 1 sf check "$WORK/plant-$what/out"
done
py expect "$LOGS/check-copy.log" ja 'shows de|identical image'
py expect "$LOGS/check-delete.log" tr 'missing'
fi

if [ "$ANDROID" = 1 ]; then
phase "android: build the fixture app"
mkdir -p "$WORK/proj-android"
APK=$WORK/build-android/FleetFixture.apk
step android-build 0 sh "$ROOT/tools/fixture-app-android/build.sh" "$WORK/build-android"
[ "$LAST_RC" = 0 ] || finish
[ -s "$APK" ] && ok "android build: $APK exists" || { bad "android build: no $APK"; finish; }

phase "android: shotfleet init"
step android-init 0 sf init "$APK" --dir "$WORK/proj-android"
[ "$LAST_RC" = 0 ] || finish
[ -f "$WORK/proj-android/shotfleet.toml" ] && [ -f "$WORK/proj-android/flow.yaml" ] && ok "android init wrote shotfleet.toml and flow.yaml" || { bad "android init wrote no config or flow"; finish; }
APKLINE=$(grep '^apk = ' "$WORK/proj-android/shotfleet.toml" || true)
[ -n "$APKLINE" ] || { bad "android init's config has no apk line"; finish; }
# parallel = 2: two emulators, two rounds; a busy Mac boots two much more reliably than four
{ printf '[android]\n%s\n' "$APKLINE"; cat <<'TOML'
devices = ["phone"]
locales = ["de", "ja", "ar", "tr"]
TOML
printf 'parallel = %s\n' "${SHOTFLEET_E2E_PARALLEL:-2}"  # 1 for a 2-core machine: two emulators there hit "Process system isn't responding"
hooks_toml; } > "$WORK/proj-android/shotfleet.toml.new" && mv "$WORK/proj-android/shotfleet.toml.new" "$WORK/proj-android/shotfleet.toml"
flow_yaml "$WORK/proj-android"

phase "android: shotfleet doctor"
step android-doctor 0 sf doctor
grep -q 'Android: ready' "$LOGS/android-doctor.log" && ok "doctor says Android: ready" || bad "doctor says Android: ready" "see $LOGS/android-doctor.log"

phase "android: shotfleet run (phone emulators)"
EMUS=1
step android-run 0 sf run "$WORK/proj-android/shotfleet.toml" --locales de,ja,ar,tr
AOUT=$WORK/proj-android/out

phase "android: shotfleet check"
step android-check 0 sf check "$AOUT"

phase "android: shotfleet export --fastlane"
step android-export 0 sf export "$AOUT" --fastlane "$WORK/fastlane-android"

phase "android: assertions on the output"
py tree --platform android --out "$AOUT" --fastlane "$WORK/fastlane-android" --hooks "$WORK/proj-android/hooks.log" --locales de,ja,ar,tr --repo "$ROOT"

phase "android: planted failures (copies of the output, the real output is untouched)"
for what in copy delete; do
  mkdir -p "$WORK/plant-android-$what"; cp -R "$AOUT" "$WORK/plant-android-$what/out"; rm -rf "$WORK/plant-android-$what/out/.work" "$WORK/plant-android-$what/out/phone/.work"
  py "plant-$what" "$WORK/plant-android-$what/out"
  step "android-check-$what" 1 sf check "$WORK/plant-android-$what/out"
done
py expect "$LOGS/android-check-copy.log" ja 'shows de|identical image'
py expect "$LOGS/android-check-delete.log" tr 'missing'
fi
finish

: <<'__PY__'
"""Assertions for tools/fixture-e2e.sh. Every check prints one line, 'PASS <what>' or 'FAIL <what>: <why>'; exit 1 if any failed.

    e2e_assert.py tree [--platform ios|android] --out OUT --fastlane DIR --hooks FILE --locales de,ja --repo REPO
    e2e_assert.py plant-copy OUT | plant-delete OUT | expect FILE LOCALE REGEX | sims
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

SHOTS = ("01_welcome", "02_settings")
WORDS = {"de": ("Weiter", "Fertig")}  # German for the fixture's 'Next' and 'Done' buttons, one per screenshot
LISTING = {"de": "de-DE", "ja": "ja", "ar": "ar-SA", "tr": "tr"}  # the App Store listing folder fastlane deliver uses
PLAY_LISTING = {"de": "de-DE", "ja": "ja-JP", "ar": "ar", "tr": "tr-TR"}  # the Google Play one fastlane supply uses
MIN_BYTES = 5000  # a real simulator screenshot is hundreds of KB; this only rejects empty and truncated files
POOLS = ("shotfleet-iphone-", "shotfleet-ipad-")  # the simulators the script's own device types create


def device_dirs(out):
    out = Path(out)
    return [out] if (out / "run.json").is_file() else sorted(d for d in out.iterdir() if (d / "run.json").is_file())


def png_ok(path):
    p = Path(path)
    if not p.is_file(): return "missing"
    data = p.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n": return "not a PNG"
    w, h = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if len(data) < MIN_BYTES or min(w, h) < 300: return f"too small ({len(data)} bytes, {w}x{h})"
    return None


def default_ocr(path, repo):
    """The OCR shotfleet's own check uses (macOS Vision through ocr.swift)."""
    sys.path.insert(0, str(repo)); import shotfleet as sf
    return sf.read_text(sf.ocr_tool(), path).get("text", "")


def text_of(png, ocr):
    """What the screen shows: the app's own text capture when the run saved one (what check prefers), else OCR."""
    f = Path(png).with_suffix(".texts.json")
    if f.is_file():
        try:
            if text := "\n".join(json.loads(f.read_text())).strip(): return text
        except ValueError: pass
    return ocr(png)


def has_copies(d, locales, shot):
    """True if this screen's image is byte-identical in two language folders."""
    imgs = [(d / "raw" / lp / f"{shot}.png").read_bytes() for lp in locales if (d / "raw" / lp / f"{shot}.png").is_file()]
    return len(set(imgs)) < len(imgs)


def tree(out, fastlane, hooks, locales, ocr, platform="ios"):
    """[(what, ok, why)] for a finished run, check and export."""
    res, devs = [], device_dirs(out)
    names = [d.name for d in devs]
    if platform == "android": res.append(("a phone set in the output", names == ["phone"], names or "no device folders"))
    else: res.append(("an iPhone and an iPad set in the output", any("iphone" in n for n in names) and any("ipad" in n for n in names), names or "no device folders"))
    want = {f"{s}.png" for s in SHOTS}
    for d in devs:
        have = {lp: sorted(p.name for p in (d / "raw" / lp).glob("*.png")) for lp in locales}
        wrong = {lp: h for lp, h in have.items() if set(h) != want or len(h) != len(SHOTS)}
        res.append((f"{d.name}: {len(SHOTS)} screenshots in every language", not wrong, f"wrong or missing in {wrong}"))
        bad = {f"{lp}/{n}": e for lp in locales for n in sorted(want) if (e := png_ok(d / "raw" / lp / n))}
        res.append((f"{d.name}: every raw PNG exists and is a real image", not bad, bad))
        shared = [shot for shot in SHOTS if has_copies(d, locales, shot)]
        res.append((f"{d.name}: no two languages share an identical image", not shared, shared))
        for word, shot in zip(WORDS["de"], SHOTS):
            png = d / "raw" / "de" / f"{shot}.png"
            text = text_of(png, ocr) if png.is_file() else ""
            res.append((f"{d.name}: de/{shot}.png shows '{word}'", word.casefold() in text.casefold(), f"text was {text[:120]!r}"))
        try: problems = json.loads((d / "check.json").read_text())["problems"]
        except (OSError, ValueError, KeyError): problems = ["no readable check.json"]
        res.append((f"{d.name}: the report has 0 problems", not problems, problems))
        try: ran = json.loads((d / "run.json").read_text())["locales"]
        except (OSError, ValueError, KeyError): ran = {}
        notok = [lp for lp in locales if not ran.get(lp, {}).get("ok")]
        res.append((f"{d.name}: run.json has every language captured ok", not notok, f"not ok: {notok}"))
    for lp in locales:
        listing = PLAY_LISTING.get(lp, lp) if platform == "android" else LISTING.get(lp, lp)
        folder = Path(fastlane) / ("metadata/android" if platform == "android" else "screenshots") / listing
        if platform == "android": folder = folder / "images/phoneScreenshots"
        need = sorted(f"{n}_{s}.png" for n in names for s in SHOTS)
        absent = [f for f in need if png_ok(folder / f)]
        res.append((f"export: {listing} has {len(need)} screenshots (one set per device)", not absent, f"missing or empty: {absent}"))
    log = Path(hooks).read_text() if Path(hooks).is_file() else ""
    for ev, pat in (("before_run", r"^before_run locales="), ("after_run", r"^after_run exit=0 problems=0$"),
                    ("before_export", r"^before_export$"), ("after_export", r"^after_export exit=0$")):
        res.append((f"hook {ev} fired (hooks.log)", bool(re.search(pat, log, re.M)), f"hooks.log was {log!r}"))
    return res


def plant(out, how):
    """Break a copy of the output the way a real mistake would: German over Japanese, or one screenshot gone. Returns what it did."""
    d = device_dirs(out)[0]
    if how == "copy": src, dst = d / "raw/de" / f"{SHOTS[0]}.png", d / "raw/ja" / f"{SHOTS[0]}.png"
    else: src, dst = None, d / "raw/tr" / f"{SHOTS[1]}.png"
    for suffix in (".png", ".texts.json"):  # the in-app text capture travels with the picture, as it would in a real mix-up
        s, t = (src.with_suffix(suffix) if src else None), dst.with_suffix(suffix)
        if how == "copy" and s.is_file(): t.write_bytes(s.read_bytes())
        else: t.unlink(missing_ok=True)  # (delete; or a copy of a picture that has no text capture)
    return f"{how}: {dst.relative_to(Path(out))}"


def expect(output, locale, pattern):
    """(ok, why): the check output has a line naming this locale ('ja/..' or 'ja:') that matches the pattern."""
    lines = [l for l in output.splitlines() if re.search(rf"(^|[\s,\-]){re.escape(locale)}[/:]", l) and re.search(pattern, l)]
    return bool(lines), f"no line names {locale} with /{pattern}/; got: {output[-400:]!r}"


def booted_pool_sims(devices_json):
    """UDIDs of booted simulators named like our own pools (shotfleet-iphone-*, shotfleet-ipad-*); never anyone else's."""
    found = []
    for devs in json.loads(devices_json or "{}").get("devices", {}).values():
        found += [d["udid"] for d in devs if d.get("state") == "Booted" and d.get("name", "").startswith(POOLS)]
    return found


def report(results):
    for what, ok, why in results: print(f"PASS {what}" if ok else f"FAIL {what}: {why}")
    return 0 if all(ok for _, ok, _ in results) else 1


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tree")
    for k in ("out", "fastlane", "hooks", "locales", "repo"): t.add_argument("--" + k, required=True)
    t.add_argument("--platform", choices=("ios", "android"), default="ios")
    for k in ("plant-copy", "plant-delete"): sub.add_parser(k).add_argument("out")
    e = sub.add_parser("expect"); [e.add_argument(k) for k in ("file", "locale", "pattern")]
    sub.add_parser("sims")
    a = ap.parse_args(argv)
    if a.cmd == "tree":
        return report(tree(a.out, a.fastlane, a.hooks, a.locales.split(","), lambda p: default_ocr(p, a.repo), a.platform))
    if a.cmd.startswith("plant-"):
        print(plant(a.out, a.cmd[6:])); return 0
    if a.cmd == "expect":
        ok, why = expect(Path(a.file).read_text(), a.locale, a.pattern)
        return report([(f"check named {a.locale} for a planted defect ({a.pattern})", ok, why)])
    r = subprocess.run(["xcrun", "simctl", "list", "devices", "booted", "-j"], capture_output=True, text=True)
    print("\n".join(booted_pool_sims(r.stdout))); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
__PY__
