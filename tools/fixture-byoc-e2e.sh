#!/bin/sh
# Device test for "bring your own capture" on iOS ([capture]): shotfleet runs tools/fixture-app's own XCUITest target
# (tools/fixture-app/UITests) on 2 simulators at once, de and ja, and collects and checks what the tests saved.
#
#   SHOTFLEET_E2E=1 tools/fixture-byoc-e2e.sh [--keep]
#
#   1. attachments: build-for-testing once, then `run` with [capture] (ScreenshotTests, XCTAttachment) in de+ja, 2 simulators
#   2. fastlane:    `run --no-build` with SnapshotStyleTests (PNGs in ~/Library/Caches/tools.fastlane/screenshots, like
#                   SnapshotHelper); the folder is left as it was found
#   3. no proof:    `run --no-build` with NoKeepTests (an attachment without .keepAlways): the test passes, the run must fail
#
# It BOOTS iOS SIMULATORS (shotfleet's own pool, shotfleet-1 and shotfleet-2, shut down again at the end), so it refuses to run
# without SHOTFLEET_E2E=1. Run it on a quiet Mac, under the device lock (docs/device-queue.md), not while another run uses
# simulators. About 5 minutes (E4 measured: build 20 s, boot 2 simulators 62 s, a cold run 45 s, warm runs 15 s). Hard limit:
# the whole script is stopped after SHOTFLEET_E2E_LIMIT_S seconds (default 1800); each language's test after 300 s ([capture]
# timeout) or 240 s without progress (stall_s); the build after shotfleet's own 60 min. Needs Xcode with an iOS runtime;
# the project is generated from tools/fixture-app/project.yml (committed, so xcodegen isn't needed).
# --keep keeps the temp work dir (it is also kept when anything fails). Exit 0 only if every assertion passed.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
KEEP=0
for a in "$@"; do
  case $a in
    --keep) KEEP=1 ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "fixture-byoc-e2e: unknown option $a (try --help)" >&2; exit 2 ;;
  esac
done
if [ "${SHOTFLEET_E2E:-}" != 1 ]; then
  echo "fixture-byoc-e2e: refusing to run. This test boots 2 iOS simulators for about 5 minutes and must not run while another" >&2
  echo "session uses them. Run it as: SHOTFLEET_E2E=1 $0" >&2
  exit 2
fi
[ "$(uname)" = Darwin ] || { echo "fixture-byoc-e2e: needs a Mac with Xcode (iOS simulators)" >&2; exit 2; }
command -v xcodebuild >/dev/null || { echo "fixture-byoc-e2e: xcodebuild not found; install Xcode" >&2; exit 2; }

# ---- pre-flight: nothing is built or booted before these pass ----
TMP=${TMPDIR:-/tmp}
free_kb=$(df -Pk "$TMP" | awk 'NR==2{print $4}')
[ "$free_kb" -ge 5242880 ] || { echo "fixture-byoc-e2e: only $((free_kb / 1048576)) GB free in $TMP, need 5 GB" >&2; exit 2; }
level=$(sysctl -n kern.memorystatus_vm_pressure_level 2>/dev/null || echo 1)
[ "$level" != 4 ] || { echo "fixture-byoc-e2e: memory pressure is critical; free memory first" >&2; exit 2; }
load=$(sysctl -n vm.loadavg | awk '{printf "%d", $2}')
[ "$load" -lt 300 ] || { echo "fixture-byoc-e2e: 1-minute load is $load (limit 300); wait for a quieter Mac" >&2; exit 2; }
if xcrun simctl list devices booted | grep -Eq '^ +shotfleet-[0-9]+ \('; then
  echo "fixture-byoc-e2e: a shotfleet simulator is already booted (another run?). Wait for it to finish." >&2; exit 2
fi

WORK=$(mktemp -d "$TMP/shotfleet-byoc-e2e.XXXXXX"); LOGS=$WORK/logs; mkdir -p "$LOGS" "$WORK/proj"
PASS=0; FAIL=0; LAST_RC=0; T0=$(date +%s); SIMS=0
LIMIT=${SHOTFLEET_E2E_LIMIT_S:-1800}
# the shell runs its TERM trap only after the running command ends, so the running shotfleet gets TERM too (it shuts its simulators down)
( sleep "$LIMIT"; echo "fixture-byoc-e2e: hard limit of $LIMIT s reached, stopping" >&2; kill -TERM $$; pkill -TERM -P $$ ) & WATCHDOG=$!
FL=$HOME/Library/Caches/tools.fastlane/screenshots
[ -d "$FL" ] && FL_BEFORE=yes || FL_BEFORE=no

cleanup() {
  kill "$WATCHDOG" 2>/dev/null || true
  # ponytail: shotfleet shuts its pool down itself; this only catches an interrupted run. Pre-flight proved none was booted.
  if [ "$SIMS" = 1 ]; then
    for u in $(xcrun simctl list devices booted | sed -nE 's/^ +shotfleet-[0-9]+ \(([0-9A-F-]{36})\).*/\1/p'); do xcrun simctl shutdown "$u" >/dev/null 2>&1 || true; done
  fi
  if [ "$KEEP" = 1 ] || [ "$FAIL" -gt 0 ]; then echo "work dir kept: $WORK"; else rm -rf "$WORK"; fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM

ok() { PASS=$((PASS + 1)); echo "PASS $1"; }
bad() { FAIL=$((FAIL + 1)); echo "FAIL $1${2:+: $2}"; }
check() { if eval "$2"; then ok "$1"; else bad "$1"; fi; }
step() {  # step NAME WANT_EXIT cmd...: output in logs/NAME.log, assert the exit code
  name=$1; want=$2; shift 2; LAST_RC=0; t=$(date +%s)
  echo "== $name"
  "$@" >"$LOGS/$name.log" 2>&1 || LAST_RC=$?
  if [ "$LAST_RC" = "$want" ]; then ok "$name exits $want ($(($(date +%s) - t)) s)"
  else bad "$name exits $want" "got $LAST_RC, log $LOGS/$name.log"; tail -n 15 "$LOGS/$name.log" | sed 's/^/     | /'; fi
}
sf() { if [ -n "${SHOTFLEET_BIN:-}" ]; then "$SHOTFLEET_BIN" "$@"; else python3 "$ROOT/shotfleet.py" "$@"; fi; }
config() {  # config OUT TESTS SCREENSHOTS
  cat > "$WORK/proj/shotfleet.toml" <<TOML
[ios]
locales = ["de", "ja"]
parallel = 2
out = "$1"
stall_s = 240

[capture]
build = "xcodebuild build-for-testing -project '$ROOT/tools/fixture-app/FleetFixture.xcodeproj' -scheme FleetFixture -destination 'generic/platform=iOS Simulator' -derivedDataPath '$WORK/build' CODE_SIGNING_ALLOWED=NO ARCHS=arm64"
xctestrun = "$WORK/build/Build/Products/*.xctestrun"
only_testing = ["FleetFixtureUITests/$2"]
screenshots = "$3"
timeout = 300
TOML
}
shots_ok() {  # shots_ok OUT: both languages have both screens, and they differ between the languages
  o=$WORK/proj/$1
  for lp in de ja; do for s in 01_welcome 02_settings; do check "$1: raw/$lp/$s.png" "[ -s '$o/raw/$lp/$s.png' ]"; done; done
  check "$1: de and ja screenshots differ" "! cmp -s '$o/raw/de/01_welcome.png' '$o/raw/ja/01_welcome.png'"
  check "$1: run.json says both languages ok" "python3 -c \"import json,sys; r=json.load(open('$o/run.json')); sys.exit(0 if all(v['ok'] and v['screenshots'] == 2 for v in r['locales'].values()) else 1)\""
  check "$1: no .xctestrun copies left beside the original" "[ -z \"\$(ls '$WORK'/build/Build/Products/*.shotfleet-* 2>/dev/null)\" ]"
}

echo "work dir: $WORK"
SIMS=1
config out-attachments ScreenshotTests attachments
step run-attachments 0 sf run "$WORK/proj/shotfleet.toml"
shots_ok out-attachments
check "the build ran once" "[ -s '$WORK/proj/out-attachments/build.log' ]"

config out-fastlane SnapshotStyleTests fastlane
step run-fastlane 0 sf run "$WORK/proj/shotfleet.toml" --no-build
shots_ok out-fastlane
[ -d "$FL" ] && FL_AFTER=yes || FL_AFTER=no
check "the fastlane folder is as it was (existed: $FL_BEFORE)" "[ '$FL_BEFORE' = '$FL_AFTER' ]"

config out-nokeep NoKeepTests attachments
step run-nokeep 1 sf run "$WORK/proj/shotfleet.toml" --no-build
check "a passing test that saved nothing is a failed language" "grep -q 'saved no screenshots' '$LOGS/run-nokeep.log'"

total=$(($(date +%s) - T0))
echo "total $((total / 60)) min $((total % 60)) s"
if [ "$FAIL" = 0 ] && [ "$PASS" -gt 0 ]; then echo "PASS: all $PASS assertions passed"; exit 0; fi
echo "FAIL: $FAIL of $((PASS + FAIL)) assertions failed"; exit 1
