#!/bin/sh
# Minimal repro for "shotfleet run did not finish on an iOS 27 simulator" (research/xcode-27-ios27-attempt-2026-10-05.md):
# ONE iOS 27 simulator, ONE language, every step killed at its own limit, 15 minutes in all. Run it on a quiet Mac, holding the
# device lock (/tmp/shotfleet-devices.lock), after `xcrun simctl list runtimes` shows an iOS 27 runtime that is Ready.
#
#   IOS27_REPRO=1 tools/ios27-repro.sh [outdir]       (prints one line per step; progress samples go to outdir/progress.log)
#   REPRO_MAESTRO_BIN_DIR=/path/to/maestro-2.11.0/bin IOS27_REPRO=1 tools/ios27-repro.sh   (puts that Maestro first on PATH)
#
# It boots ONE simulator (shotfleet's own pool name shotfleet-iphone-17-pro-max-1 on the iOS 27 runtime) and deletes it again,
# by UDID, if it was not there before. It never touches a runtime. Nothing it prints counts as a pass unless `run exits 0` is PASS.
set -u
[ "${IOS27_REPRO:-}" = 1 ] || { echo "ios27-repro: boots a simulator; set IOS27_REPRO=1 to run it" >&2; exit 2; }
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:-$(mktemp -d "${TMPDIR:-/tmp}/ios27-repro.XXXXXX")}; mkdir -p "$OUT"
RT=com.apple.CoreSimulator.SimRuntime.iOS-27-0
[ -n "${REPRO_MAESTRO_BIN_DIR:-}" ] && PATH="$REPRO_MAESTRO_BIN_DIR:$PATH"
xcrun simctl list runtimes | grep -q "$RT" || { echo "ios27-repro: no iOS 27 runtime installed" >&2; exit 2; }
START=$(date +%s); T0=$START
say() { printf '%s +%4ss  %s\n' "$(date +%T)" "$(( $(date +%s) - START ))" "$*" | tee -a "$OUT/summary.log"; }
# run_limited SECONDS LOGFILE COMMAND...  -> exit status of the command, 124 when it was killed at the limit
run_limited() { lim=$1; lg=$2; shift 2; "$@" >"$lg" 2>&1 & p=$!; i=0
  while kill -0 $p 2>/dev/null && [ $i -lt $lim ]; do sleep 1; i=$((i+1)); done
  if kill -0 $p 2>/dev/null; then pkill -P $p 2>/dev/null; kill $p 2>/dev/null; sleep 2; kill -9 $p 2>/dev/null; return 124; fi
  wait $p; }
devs() { xcrun simctl list devices -j | python3 -c "import json,sys; print('\n'.join(x['udid'] for x in json.load(sys.stdin)['devices'].get('$RT',[])))"; }
devs | sort > "$OUT/devices-before.txt"
cleanup() {
  [ -n "${SAMPLER:-}" ] && kill "$SAMPLER" 2>/dev/null
  for u in $(devs); do grep -q "$u" "$OUT/devices-before.txt" && continue; xcrun simctl shutdown "$u" 2>/dev/null; xcrun simctl delete "$u" && say "deleted simulator $u (created by this run)"; done
  say "total $(( $(date +%s) - T0 )) s; output in $OUT"
}
trap cleanup EXIT INT TERM

say "load $(sysctl -n vm.loadavg) | $(sysctl vm.swapusage | cut -d= -f2- | cut -c1-70) | $(df -h / | tail -1 | awk '{print $4" free"}')"
say "Xcode $(xcodebuild -version | tr '\n' ' ') | macOS $(sw_vers -productVersion) | Maestro $(maestro --version 2>&1 | tail -1)"

W="$OUT/work"; mkdir -p "$W"
run_limited 90 "$OUT/build.log" sh "$ROOT/tools/fixture-app/build.sh" "$W/build"; rc=$?; say "build rc=$rc (limit 90 s)"; [ $rc = 0 ] || exit 1
run_limited 60 "$OUT/init.log" python3 "$ROOT/shotfleet.py" init "$W/build/FleetFixture.app" --dir "$W/proj"; rc=$?; say "init rc=$rc (limit 60 s)"; [ $rc = 0 ] || exit 1
APPLINE=$(grep '^app = ' "$W/proj/shotfleet.toml") || { say "init wrote no app line"; exit 1; }
printf '[ios]\n%s\ndevice_types = ["iPhone 17 Pro Max"]\nruntime = "%s"\nlocales = ["de"]\n' "$APPLINE" "$RT" > "$W/proj/shotfleet.toml"
cp "$W/proj/flow.yaml" "$OUT/flow.yaml"
run_limited 180 "$OUT/doctor.log" python3 "$ROOT/shotfleet.py" doctor; rc=$?; say "doctor rc=$rc (limit 180 s)"   # 5 s on iOS 26.4 at load ~120, 74 s on iOS 27 at load ~700

# progress sampler: every 15 s, the facts a stall needs (simulator state, driver processes, shotfleet/maestro alive).
# The driver-port probe is best effort: port 22087 and /deviceInfo are my recollection of Maestro's iOS driver, not verified here.
( while :; do
    { echo "== $(date +%T) load $(sysctl -n vm.loadavg) swap $(sysctl vm.swapusage | cut -d= -f2- | cut -c1-40)"
      xcrun simctl list devices | grep -E "shotfleet-iphone-17-pro-max-1 " | cut -c1-110
      pgrep -fl "xcodebuild.*maestro-driver" | cut -c1-90
      pgrep -fl "maestro.cli" | cut -c1-70
      printf 'driver port 22087: '; curl -s -m 3 -o /dev/null -w '%{http_code}\n' http://localhost:22087/deviceInfo 2>&1 | head -1
      ls "$W/proj" 2>/dev/null | tr '\n' ' '; echo; } >> "$OUT/progress.log"; sleep 15; done ) &
SAMPLER=$!

run_limited 600 "$OUT/run.log" python3 "$ROOT/shotfleet.py" run "$W/proj/shotfleet.toml" --locales de --parallel 1; rc=$?
if [ $rc = 124 ]; then say "FAIL run killed at its 600 s limit: it did not finish (see progress.log, run.log)"
elif [ $rc = 0 ]; then say "PASS run exits 0"; else say "FAIL run exits $rc (see run.log)"; fi
tail -5 "$OUT/run.log" | cut -c1-160 | while read -r l; do say "run.log: $l"; done
exit $rc
