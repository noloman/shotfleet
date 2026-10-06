#!/bin/sh
# Release candidate: build the real release artifact locally and test the FROZEN program (not `python3 shotfleet.py`), as far as
# it can be tested without the network accounts. Roadmap gates 5 (licence) and 6 (release build) in STATUS.md.
#
#   SHOTFLEET_RC=1 tools/release-candidate.sh [--no-sign] [--keep] [--reuse WORKDIR]
#
# It builds with PyInstaller (hundreds of MB, several minutes, `pip install` needs the network), so it refuses to run without
# SHOTFLEET_RC=1. Nothing is deployed, pushed, uploaded or notarized: no `notarytool`, no Apple submission, no real Gumroad call. The licence is tested against a local fake server (the Python at the end of this file); the build gets a TEST
# GUMROAD_PRODUCT_ID in a temp COPY of shotfleet.py (the repo file is never edited) so the licence gate is ON. No simulator boots.
#   --no-sign        skip signing even when a Developer ID Application identity is in the keychain
#   --keep           keep the work dir (it is also kept when a check fails); --reuse WORKDIR runs the checks on a kept build
# The two things this cannot prove: Apple's notarization verdict and a real Gumroad key. Exit 0 only if every check passed.
SELF=$(cd "$(dirname "$0")" && pwd)/$(basename "$0")
ROOT=$(dirname "$(dirname "$SELF")")
helper() { sed -n '/^: <<.__PY__.$/,/^__PY__$/p' "$SELF" | sed '1d;$d' > "$1"; }  # the Python helpers are the end of this file (tests/test_release_candidate.py loads them the same way)
KEEP=0; SIGN=1; REUSE=
while [ $# -gt 0 ]; do
  case $1 in
    --keep) KEEP=1 ;;
    --no-sign) SIGN=0 ;;
    --reuse) shift; REUSE=${1:?--reuse needs a work dir} ;;
    -h|--help) sed -n '2,15p' "$SELF" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "release-candidate: unknown option $1 (try --help)" >&2; exit 2 ;;
  esac
  shift
done
if [ "${SHOTFLEET_RC:-}" != 1 ]; then
  echo "release-candidate: refusing to run. It builds the release with PyInstaller (hundreds of MB, minutes, needs pip's network)" >&2
  echo "and installs nothing outside a temp dir. Run it as: SHOTFLEET_RC=1 $0" >&2
  exit 2
fi
[ "$(uname -s)-$(uname -m)" = Darwin-arm64 ] || { echo "release-candidate: needs an Apple silicon Mac" >&2; exit 2; }
for t in swiftc python3 codesign shasum curl xattr spctl; do command -v "$t" >/dev/null 2>&1 || { echo "release-candidate: $t not found" >&2; exit 2; }; done
TMP=${TMPDIR:-/tmp}; TMP=${TMP%/}
free_kb=$(df -Pk "$TMP" | awk 'NR==2{print $4}')
[ -n "$REUSE" ] || [ "$free_kb" -ge 3145728 ] || { echo "release-candidate: only $((free_kb / 1048576)) GB free in $TMP, need 3 GB" >&2; exit 2; }

if [ -n "$REUSE" ]; then WORK=$REUSE; KEEP=1; else WORK=$(mktemp -d "$TMP/shotfleet-rc.XXXXXX"); fi
SRC=$WORK/src; RUN=$WORK/run; PY=$WORK/rc_helper.py
helper "$PY"
rm -rf "$RUN"; mkdir -p "$RUN"
PID1=; PID2=
N=0; BAD=0
cleanup() {
  [ -z "$PID1" ] || kill "$PID1" 2>/dev/null; [ -z "$PID2" ] || kill "$PID2" 2>/dev/null
  if [ "$KEEP" = 1 ] || [ "$BAD" -gt 0 ]; then echo "work dir kept: $WORK"; else rm -rf "$WORK"; fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM
ok() { N=$((N + 1)); echo "  ok    $*"; }
skip() { echo "  SKIP  $*"; }
fail() { N=$((N + 1)); BAD=$((BAD + 1)); echo "  FAIL  $*"; }
die() { echo "release-candidate: $*" >&2; BAD=$((BAD + 1)); exit 1; }
has() { printf '%s' "$OUT" | grep -qF -- "$1"; }
# chk LABEL WANT_EXIT [SUBSTRING...]: the last command's exit code and output (in $RC, $OUT)
chk() {
  _l=$1; _rc=$2; shift 2; _b=
  [ "$RC" = "$_rc" ] || _b="exit $RC, wanted $_rc; "
  for _s in "$@"; do has "$_s" || _b="${_b}missing '$_s'; "; done
  if [ -z "$_b" ]; then ok "$_l"; else fail "$_l: $_b"; fi
}
nothas() { if has "$2"; then fail "$1: output has '$2'"; else ok "$1"; fi; }
# show LABEL CMD...: run any command, print it and its (trimmed) output
show() { echo "\$ $*"; OUT=$("$@" 2>&1); RC=$?; printf '%s\n' "$OUT" | head -${SHOWN:-8} | sed 's/^/    /'; echo "    [exit $RC]"; }
API=; SFX=
# sfrun HOME ARGS...: the frozen program in a clean environment, HOME = a temp dir (the licence file lives under HOME)
sfrun() {
  _h=$1; shift
  echo "\$ shotfleet $*   (HOME=${_h#$RUN/})${SFX:+ $SFX}"
  OUT=$(eval "env -i HOME=\"\$_h\" PATH=\"\$PATH\" ${API:+SHOTFLEET_GUMROAD_API=\"\$API\"} $SFX \"\$BIN\" \"\$@\"" 2>&1); RC=$?
  printf '%s\n' "$OUT" | head -${SHOWN:-8} | sed 's/^/    /'; echo "    [exit $RC]"
}
free_port() { python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])'; }
wait_url() { _i=0; while [ $_i -lt 50 ]; do curl -s -o /dev/null "$1" 2>/dev/null && return 0; _i=$((_i + 1)); sleep 0.1; done; return 1; }
with_timeout() { _s=$1; shift; ( "$@" & _p=$!; ( sleep "$_s"; kill "$_p" 2>/dev/null ) & _w=$!; wait "$_p"; _r=$?; kill "$_w" 2>/dev/null; exit $_r ); }
state() { curl -s "$BASE/_state"; }
uses() { state | python3 -c 'import json, sys; print(json.load(sys.stdin)["uses"][sys.argv[1]])' "$1"; }
ctl() { curl -s -X POST -d "$1" "$BASE/_ctl" >/dev/null; }

GOOD=ABCDEF12-34567890-ABCDEF12-34567890; REFUNDED=11111111-22222222-33333333-44444444; UNKNOWN=00000000-00000000-00000000-00000001
PRODUCT_ID=RCTESTPRODUCT0001abc==  # a TEST product id: the fake server only knows keys of this product

echo "== release candidate, $(date '+%Y-%m-%d %H:%M'), work dir $WORK"
echo "   disk free in $TMP: $((free_kb / 1048576)) GB"

# ------------------------------------------------------------------ 1. build
ID=
if [ "$SIGN" = 1 ]; then
  ID=$(security find-identity -v -p codesigning 2>/dev/null | sed -n 's/^ *[0-9]*) [0-9A-F]\{40\} "\(Developer ID Application:.*\)"$/\1/p' | head -1)
fi
if [ -n "$ID" ]; then echo "== signing identity: $ID (build.sh signs; NOTARY_PROFILE is unset, so nothing is submitted to Apple)"
else echo "== signing identity: none used (${REUSE:+reused build; }--no-sign or no 'Developer ID Application' in 'security find-identity -v -p codesigning'); the build stays unsigned"; fi
if [ -z "$REUSE" ]; then
  echo "== build (a temp copy of the repo's shotfleet.py with GUMROAD_PRODUCT_ID = $PRODUCT_ID; the repo file is not touched)"
  mkdir -p "$SRC" && cp "$ROOT/shotfleet.py" "$ROOT/ocr.swift" "$SRC/" && cp -R "$ROOT/skill" "$ROOT/packaging" "$ROOT/tools" "$SRC/" || die "can't copy the sources"
  sed -i '' "s|^GUMROAD_PRODUCT_ID = .*|GUMROAD_PRODUCT_ID = \"$PRODUCT_ID\"  # release-candidate TEST id|" "$SRC/shotfleet.py"
  grep -qF "GUMROAD_PRODUCT_ID = \"$PRODUCT_ID\"" "$SRC/shotfleet.py" || die "the test product id did not land in the copy"
  [ "$(diff "$ROOT/shotfleet.py" "$SRC/shotfleet.py" | grep -c '^[<>]')" = 2 ] && ok "the build copy differs from shotfleet.py in exactly one line (the product id)" || fail "the build copy differs from shotfleet.py in more than the product id line"
  T0=$(date +%s)
  (cd "$SRC" && env -u NOTARY_PROFILE ${ID:+DEVELOPER_ID="$ID"} sh packaging/build.sh) > "$WORK/build.log" 2>&1; BRC=$?
  echo "$((($(date +%s) - T0))) s" > "$WORK/build-seconds"
  tail -5 "$WORK/build.log" | sed 's/^/    /'; echo "    [build exit $BRC, $(cat "$WORK/build-seconds")]"
  [ "$BRC" = 0 ] && ok "packaging/build.sh built the release in $(cat "$WORK/build-seconds")" || { fail "packaging/build.sh failed (log: $WORK/build.log)"; exit 1; }
fi
VERSION=$(sed -n 's/^VERSION = "\(.*\)"/\1/p' "$SRC/shotfleet.py")
DIST=$SRC/dist; APP=$DIST/shotfleet; BIN=$APP/shotfleet; TAR=$DIST/shotfleet-$VERSION-macos-arm64.tar.gz
[ -x "$BIN" ] && [ -f "$TAR" ] || die "no $BIN or $TAR"
echo "== artifact: $(du -sh "$APP" | cut -f1) folder, $(du -sh "$TAR" | cut -f1) tarball ($(wc -c < "$TAR" | tr -d ' ') bytes), version $VERSION, $(find "$APP" -type f | wc -l | tr -d ' ') files"
file -b "$BIN" | sed 's/^/   /'

# ------------------------------------------------------------------ 2. what is inside the folder
echo "== bundle contents"
CERT=$(find "$APP" -name cacert.pem | head -1)
VENVCERT=$(ls "$SRC"/build/venv/lib/python*/site-packages/certifi/cacert.pem 2>/dev/null | head -1)
if [ -n "$CERT" ]; then ok "certifi's cacert.pem is bundled: ${CERT#$APP/} ($(wc -c < "$CERT" | tr -d ' ') bytes)"; else fail "no cacert.pem inside the onedir folder: TLS to Gumroad would fall back to the Mac's CA bundle"; fi
if [ -n "$CERT" ] && [ -n "$VENVCERT" ]; then
  [ "$(shasum -a 256 "$CERT" | cut -d' ' -f1)" = "$(shasum -a 256 "$VENVCERT" | cut -d' ' -f1)" ] && ok "the bundled bundle is the one pip installed (identical SHA-256)" || fail "bundled cacert.pem differs from the venv's certifi"
fi
[ -x "$(find "$APP" -name ocr -type f | head -1)" ] && ok "the prebuilt OCR helper is inside ($(find "$APP" -name ocr -type f | head -1 | sed "s|$APP/||"))" || fail "no OCR helper in the folder"
[ -n "$(find "$APP" -path '*skill/shotfleet/SKILL.md' | head -1)" ] && ok "the agent skills are inside" || fail "no skill folder in the bundle"

# ------------------------------------------------------------------ 3. signing, Gatekeeper
echo "== signature"
if [ -n "$ID" ]; then
  SHOWN=14 show codesign --verify --deep --strict --verbose=2 "$BIN"
  [ "$RC" = 0 ] && ok "codesign --verify --deep --strict passes on the executable" || fail "codesign --verify failed"
  SHOWN=14 show codesign -dvv "$BIN"
  has "Authority=Developer ID Application" && has "flags=0x10000(runtime)" && ok "Developer ID authority, hardened runtime" || fail "not Developer ID + hardened runtime"
  has "Timestamp=" && ok "a secure timestamp is attached (notarization needs one)" || fail "no timestamp"
  find "$APP" -type f | while IFS= read -r f; do
    file -b "$f" | grep -q Mach-O || continue
    if codesign --verify --strict "$f" >/dev/null 2>&1; then echo ok; else echo "bad ${f#$APP/}"; fi
  done > "$RUN/macho.txt"
  grep '^bad' "$RUN/macho.txt" | sed 's/^/    /'
  if grep -q '^bad' "$RUN/macho.txt"; then fail "$(grep -c '^bad' "$RUN/macho.txt") Mach-O files fail verification"; else ok "every Mach-O file in the folder verifies ($(grep -c '^ok' "$RUN/macho.txt") files)"; fi
  show codesign -d --entitlements - "$BIN"
  show spctl --assess --type execute -vv "$BIN"
  [ "$RC" != 0 ] && ok "spctl rejects it until notarized, as expected ('$(printf '%s' "$OUT" | grep -m1 'source=' )')" || ok "spctl ACCEPTS it (notarization ticket found or Gatekeeper off here)"
else skip "unsigned build: codesign and spctl checks"; fi

echo "== quarantined copy (a browser download would set this flag; run from a shell)"
Q=$RUN/quarantine; mkdir -p "$Q" && cp -R "$APP" "$Q/shotfleet"
xattr -rw com.apple.quarantine "0081;00000000;Safari;" "$Q/shotfleet"
show xattr -l "$Q/shotfleet/shotfleet"
SHOWN=6 show with_timeout 90 "$Q/shotfleet/shotfleet" --version
# Informational, not pass/fail: an unnotarized program is expected to be stopped by Gatekeeper; only a notarized one must run here.
if [ "$RC" = 0 ]; then echo "    OBSERVED: Gatekeeper did NOT block the quarantined ${ID:+signed }unnotarized program run from a shell"
else echo "    OBSERVED: the quarantined ${ID:+signed }unnotarized program did NOT run from a shell: exit $RC (137/143 = killed by Gatekeeper or by the 90 s timeout)"; fi
show xattr -l "$Q/shotfleet/shotfleet"

# ------------------------------------------------------------------ 4. the frozen program, no licence needed
echo "== frozen program: free commands"
H0=$RUN/home0; mkdir -p "$H0"
sfrun "$H0" --version
chk "--version prints the version and nothing else" 0 "shotfleet $VERSION"
[ "$OUT" = "shotfleet $VERSION" ] || fail "--version printed more than the version: $OUT"
START=$(date +%s)
SHOWN=30 sfrun "$H0" doctor
echo "    (doctor took $(($(date +%s) - START)) s; it also reads https://shotfleet.com/download/VERSION, a plain GET)"
nothas "doctor does not crash" Traceback
has "maestro" && has "java 17+" && has "xcrun simctl" && has "text recognition" && ok "doctor reports Maestro, Java, Xcode (simctl) and text recognition" || fail "doctor output lacks a tool line"
case $RC in 0|2) ok "doctor exit code is 0 or 2 (is: $RC)";; *) fail "doctor exit code $RC";; esac
printf '%s' "$OUT" | grep -q '^ok   *swiftc' && ok "doctor does not need swiftc in the frozen build (OCR helper is bundled)" || fail "doctor wants swiftc"
SK=$RUN/skills
sfrun "$H0" skill install --dir "$SK"
chk "skill install --dir copies the skills" 0 "installed $SK/shotfleet"
[ -f "$SK/shotfleet/SKILL.md" ] && [ -f "$SK/shotfleet-ci/SKILL.md" ] && [ -f "$SK/shotfleet-review/SKILL.md" ] && ok "three SKILL.md files are on disk" || fail "skills missing in $SK"
python3 "$PY" fixture "$RUN/fx"
SFX="SHOTFLEET_OCR='cat {image}.txt'"
sfrun "$H0" check "$RUN/fx/shots" --strings "$RUN/fx/locales/*/translation.json" --report "$RUN/fx/rep" --json
SFX=
chk "check finds the planted wrong-language screenshot with no licence (exit 1, JSON report)" 1 '"exit": 1' "el/2.png: shows en strings"
printf '%s' "$OUT" | python3 -c '
import json, sys
text = sys.stdin.read(); r = json.loads(text[text.index("{"):])
got = {p.split(":")[0] for p in r["problems"]}
# el/2.png is planted and en/2.png is missing; en/1.png may also be reported "no text found": macOS reads English itself and finds nothing
# in a header-only PNG, unless its text recognition is stuck (loaded Mac), when --ocr-command reads everything
assert len(r["screenshots"]) == 3 and {"el/2.png", "en"} <= got <= {"el/2.png", "en", "en/1.png"}, r
' && ok "the JSON report has 3 screenshots and the planted problems (el/2.png wrong language, en/2.png missing; en/1.png is a header-only PNG, so macOS OCR may report it blank)" || fail "unexpected check report"
[ -f "$RUN/fx/rep/index.html" ] && ok "check wrote index.html" || fail "no index.html"

# ------------------------------------------------------------------ 5. free tier (no key)
echo "== free tier on the gate-ON build (no licence file)"
python3 "$PY" freetier "$RUN/ft"
sfrun "$H0" run "$RUN/ft/shotfleet.toml"
chk "run without a key prints the note, the 2-of-3 cap and stops before any device (no simulator touched)" 2 \
  "note: \`export\` and every language in \`run\` need a licence" "free tier: capturing 2 of 3 languages (fr, it)" "none of those languages are in the app"
nothas "no simulator is booted by the free-tier run" "booting"
python3 "$PY" exportfx "$RUN/ex"
sfrun "$H0" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"
chk "export without a key is refused" 2 "need a licence: shotfleet activate <key>"
[ ! -e "$RUN/ex/fastlane" ] && ok "nothing was written to the fastlane folder" || fail "export wrote files without a licence"
sfrun "$H0" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane" --json
printf '%s' "$OUT" | grep -q '"exported"' && fail "export --json without a key exported" || ok "export --json without a key exports nothing"
sfrun "$H0" deactivate
chk "deactivate with no licence says so" 0 "no licence on this Mac"

# ------------------------------------------------------------------ 6. TLS trust
echo "== TLS: the frozen program verifies HTTPS with the bundled certifi (a plain GET target that is not Gumroad)"
API=https://example.com/v2/licenses
sfrun "$H0" activate "$GOOD"
case $OUT in
  *CERTIFICATE_VERIFY_FAILED*) fail "TLS verification failed against example.com: the bundled CA file is not used" ;;
  *answered*) ok "TLS handshake to a public HTTPS host verified (example.com answered, so the CA bundle works)" ;;
  *"can't reach"*) skip "no network here: TLS trust only proven by the bundled cacert.pem being present" ;;
  *) fail "unexpected answer from example.com: $OUT" ;;
esac
[ ! -e "$H0/Library/Application Support/shotfleet/licence.json" ] && ok "no licence file was written by the failed activation" || fail "a licence file exists after a failed activation"
API=

# ------------------------------------------------------------------ 7. licence against the fake Gumroad
echo "== licence against the local fake Gumroad API (same contract as gumroad_verify; the real API is never called)"
PF=$RUN/port; python3 "$PY" fake-gumroad "$PF" "$PRODUCT_ID" > "$RUN/fake.log" 2>&1 &
PID1=$!
_i=0; while [ ! -s "$PF" ] && [ $_i -lt 50 ]; do sleep 0.1; _i=$((_i + 1)); done
[ -s "$PF" ] || die "the fake Gumroad server did not start: $(cat "$RUN/fake.log")"
BASE=http://127.0.0.1:$(cat "$PF"); API=$BASE/v2/licenses
wait_url "$BASE/_state" || die "fake server not answering"
echo "   fake server: $API (product $PRODUCT_ID)"

H1=$RUN/home1; mkdir -p "$H1"; LIC1="$H1/Library/Application Support/shotfleet/licence.json"
sfrun "$H1" activate "$UNKNOWN"
chk "an unknown key is refused with Gumroad's message" 2 "that key didn't activate: That license does not exist for the provided product"
[ ! -e "$LIC1" ] && ok "no licence file after an unknown key" || fail "licence file after an unknown key"
sfrun "$H1" activate "$REFUNDED"
chk "a refunded key is refused" 2 "the purchase was refunded"
[ "$(uses "$REFUNDED")" = 0 ] && ok "the refused key burned no activation (uses=0)" || fail "refusal burned a use: $(uses "$REFUNDED")"
sfrun "$H1" activate "$GOOD"
chk "activate <key> works" 0 "activated on" "Thanks for buying shotfleet"
[ "$(uses "$GOOD")" = 1 ] && ok "uses=1 after the first activation" || fail "uses is $(uses "$GOOD"), wanted 1"
python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); assert d["store"] == "gumroad" and d["key"] == sys.argv[2] and "checked" in d, d' "$LIC1" "$GOOD" && ok "licence.json stored under HOME/Library/Application Support/shotfleet (store gumroad)" || fail "licence.json missing or wrong"
sfrun "$H1" activate "$GOOD"
chk "activating again on the same Mac works" 0 "activated on"
[ "$(uses "$GOOD")" = 1 ] && ok "re-activating on the same Mac burned no extra use (uses still 1)" || fail "re-activate changed uses to $(uses "$GOOD")"

SFX=; sfrun "$H1" run "$RUN/ft/shotfleet.toml"
chk "with a licence, run applies no free-tier cap or note" 2 "none of those languages are in the app"
nothas "no cap line with a licence" "free tier:"
nothas "no licence note with a licence" "note:"
sfrun "$H1" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"
chk "export is unlocked and writes the listing" 0 "exported 1 listings"
ls "$RUN/ex/fastlane/screenshots/de-DE" >/dev/null 2>&1 && ok "the screenshot is in fastlane/screenshots/de-DE" || fail "no exported file"
rm -rf "$RUN/ex/fastlane"

echo "-- weekly re-check"
python3 "$PY" age "$LIC1" 3
N0=$(state | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["calls"]))')
sfrun "$H1" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"; rm -rf "$RUN/ex/fastlane"
N1=$(state | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["calls"]))')
[ "$N1" = "$N0" ] && ok "3 days old: no network call (re-checked at most weekly)" || fail "3-day-old licence was re-checked ($N0 -> $N1 calls)"
python3 "$PY" age "$LIC1" 8
sfrun "$H1" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"; rm -rf "$RUN/ex/fastlane"
chk "8 days old: re-checked online and still valid, export works" 0 "exported 1 listings"
state | python3 -c 'import json,sys; c = json.load(sys.stdin)["calls"][-1]; assert c["increment_uses_count"] == "false", c' && ok "the re-check does not count a use (increment_uses_count=false)" || fail "the re-check counted a use"
[ "$(uses "$GOOD")" = 1 ] && ok "uses still 1 after the re-check" || fail "uses changed to $(uses "$GOOD")"
python3 -c 'import json, sys, time; d = json.load(open(sys.argv[1])); assert time.time() - d["checked"] < 120, d' "$LIC1" && ok "the stored 'checked' timestamp was refreshed" || fail "'checked' not refreshed"
echo "-- a refund after the purchase"
ctl "refund=$GOOD"; python3 "$PY" age "$LIC1" 8
sfrun "$H1" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"
chk "8 days old and the purchase was refunded since: export refused" 2 "this licence is no longer valid (the purchase was refunded)"
sfrun "$H1" run "$RUN/ft/shotfleet.toml"
chk "...and run falls back to the free tier cap" 2 "free tier: capturing 2 of 3 languages (fr, it)" "this licence is no longer valid"
ctl "unrefund=$GOOD"
echo "-- outage and offline grace"
python3 "$PY" age "$LIC1" 10; ctl "outage=1"
sfrun "$H1" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"; rm -rf "$RUN/ex/fastlane"
chk "10 days old and Gumroad answers 503: not a verdict, export works (grace)" 0 "exported 1 listings"
ctl "outage=0"
kill "$PID1" 2>/dev/null; wait "$PID1" 2>/dev/null; PID1=
sfrun "$H1" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"; rm -rf "$RUN/ex/fastlane"
chk "10 days old and the server is DOWN (connection refused): 30-day offline grace, export works" 0 "exported 1 listings"
python3 "$PY" age "$LIC1" 29
sfrun "$H1" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"; rm -rf "$RUN/ex/fastlane"
chk "29 days old and offline: still inside the grace" 0 "exported 1 listings"
python3 "$PY" age "$LIC1" 31
sfrun "$H1" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"
chk "31 days old and offline: refused" 2 "couldn't reach the licence server for 30 days"
sfrun "$H1" run "$RUN/ft/shotfleet.toml"
chk "...and run falls back to the free tier cap" 2 "free tier: capturing 2 of 3 languages (fr, it)"
# a fresh server (state starts over) for the activation count and CI key
rm -f "$PF"; python3 "$PY" fake-gumroad "$PF" "$PRODUCT_ID" > "$RUN/fake2.log" 2>&1 &
PID1=$!
_i=0; while [ ! -s "$PF" ] && [ $_i -lt 50 ]; do sleep 0.1; _i=$((_i + 1)); done
BASE=http://127.0.0.1:$(cat "$PF"); API=$BASE/v2/licenses; wait_url "$BASE/_state" || die "second fake server not answering"
echo "-- back online: re-check refreshes a stale licence again, then deactivate"
python3 "$PY" age "$LIC1" 31
sfrun "$H1" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"; rm -rf "$RUN/ex/fastlane"
chk "31 days old, server back (key valid): re-check passes and export works" 0 "exported 1 listings"
sfrun "$H1" deactivate
chk "deactivate removes the local licence and says Gumroad can't return the activation" 0 "removed from this Mac. Gumroad can't give the activation back from here" "hello@shotfleet.com"
[ ! -e "$LIC1" ] && ok "licence.json is gone" || fail "licence.json still there"
sfrun "$H1" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"
chk "export is locked again after deactivate" 2 "need a licence"

echo "-- five activations, then the sixth"
for n in 2 3 4 5; do
  mkdir -p "$RUN/home$n"
  sfrun "$RUN/home$n" activate "$GOOD"
  chk "Mac $n activates" 0 "activated on"
done
[ "$(uses "$GOOD")" = 4 ] && ok "uses=4 after four Macs on a fresh server" || fail "uses is $(uses "$GOOD")"
sfrun "$H1" activate "$GOOD"
chk "activation 5 (the former Mac 1, after deactivate) works: uses=5" 0 "activated on"
H6=$RUN/home6; mkdir -p "$H6"
sfrun "$H6" activate "$GOOD"
chk "the 6th activation is refused with the email message" 2 "this key has used all 5 activations. Email hello@shotfleet.com and I'll reset the count"
[ "$(uses "$GOOD")" = 5 ] && ok "the refusal burned nothing (uses stays 5)" || fail "uses is $(uses "$GOOD") after the refusal"
[ ! -e "$H6/Library/Application Support/shotfleet/licence.json" ] && ok "no licence file on the 6th" || fail "the 6th has a licence file"
sfrun "$H1" activate "$GOOD"
chk "a Mac that already holds the key can still re-activate with all 5 used" 0 "activated on"

echo "-- CI: SHOTFLEET_KEY (no activation slot, no licence file)"
H5=$RUN/home5; mkdir -p "$H5"
SFX="SHOTFLEET_KEY=$GOOD"; sfrun "$H5" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"; rm -rf "$RUN/ex/fastlane"
chk "export unlocked by SHOTFLEET_KEY" 0 "exported 1 listings"
[ "$(uses "$GOOD")" = 5 ] && ok "SHOTFLEET_KEY used no activation (uses still 5)" || fail "SHOTFLEET_KEY changed uses to $(uses "$GOOD")"
[ ! -e "$H5/Library/Application Support/shotfleet/licence.json" ] && ok "SHOTFLEET_KEY wrote no licence file" || fail "SHOTFLEET_KEY wrote a licence file"
SFX="SHOTFLEET_KEY=$REFUNDED"; sfrun "$H5" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"
chk "a refunded SHOTFLEET_KEY is refused" 2 "SHOTFLEET_KEY isn't a valid licence (the purchase was refunded)"
SFX="SHOTFLEET_KEY=$GOOD"; sfrun "$H5" run "$RUN/ft/shotfleet.toml"
chk "run with SHOTFLEET_KEY has no cap" 2 "none of those languages are in the app"
nothas "no cap with SHOTFLEET_KEY" "free tier:"
ctl "outage=1"; sfrun "$H5" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"; rm -rf "$RUN/ex/fastlane"
chk "a Gumroad outage does not fail a CI build with a SHOTFLEET_KEY that passed a check on this machine" 0 "exported 1 listings"
H7=$RUN/home7; mkdir -p "$H7"; sfrun "$H7" export "$RUN/ex/out" --fastlane "$RUN/ex/fastlane"
chk "...but on a machine where it never passed a check, an outage refuses it" 2 "SHOTFLEET_KEY couldn't be checked"
ctl "outage=0"
SFX=
state | python3 -c 'import json,sys; s = json.load(sys.stdin); assert all(c["product_id"] == "RCTESTPRODUCT0001abc==" for c in s["calls"]); print(len(s["calls"]), "calls, all with the build'"'"'s product id")' && ok "every call carried this build's product id and nothing else" || fail "a call had another product id"
kill "$PID1" 2>/dev/null; wait "$PID1" 2>/dev/null; PID1=

# ------------------------------------------------------------------ 8. tarball, checksum, install.sh
echo "== tarball like release.sh, served by a local http.server, installed by site/public/install.sh into a temp HOME"
SERVE=$RUN/serve; D=$SERVE/download; mkdir -p "$D" "$SERVE/download-bad"
for f in "$ROOT"/site/public/*; do [ "$(basename "$f")" = download ] || ln -s "$f" "$SERVE/"; done
cp "$TAR" "$D/shotfleet-macos-arm64.tar.gz"   # the same lines as packaging/release.sh
(cd "$D" && shasum -a 256 shotfleet-macos-arm64.tar.gz > shotfleet-macos-arm64.tar.gz.sha256); echo "$VERSION" > "$D/VERSION"
cp "$D"/* "$SERVE/download-bad/"; echo "0000000000000000000000000000000000000000000000000000000000000000  shotfleet-macos-arm64.tar.gz" > "$SERVE/download-bad/shotfleet-macos-arm64.tar.gz.sha256"
cat "$D/shotfleet-macos-arm64.tar.gz.sha256"
SP=$(free_port); python3 -m http.server "$SP" --bind 127.0.0.1 --directory "$SERVE" > "$RUN/http.log" 2>&1 &
PID2=$!; wait_url "http://127.0.0.1:$SP/download/VERSION" || die "static server not answering"
[ "$(curl -s "http://127.0.0.1:$SP/download/VERSION")" = "$VERSION" ] && ok "VERSION is served ($VERSION)" || fail "VERSION not served"
[ "$(curl -s "http://127.0.0.1:$SP/download/shotfleet-macos-arm64.tar.gz" | shasum -a 256 | cut -d' ' -f1)" = "$(cut -d' ' -f1 "$D/shotfleet-macos-arm64.tar.gz.sha256")" ] && ok "the served archive matches its .sha256 byte for byte" || fail "served archive != .sha256"
# the tarball itself: contents, and the signature survives tar
X=$RUN/untar; mkdir -p "$X" && tar -xzf "$TAR" -C "$X" && [ -x "$X/shotfleet/shotfleet" ] && ok "tarball extracts to shotfleet/shotfleet" || fail "tarball layout wrong"
if [ -n "$ID" ]; then codesign --verify --deep --strict "$X/shotfleet/shotfleet" 2>&1 && ok "the signature survives tar and extraction" || fail "signature broken by the tarball"; fi
INST=$ROOT/site/public/install.sh
LINE='for DIR in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin"; do'
grep -qxF "$LINE" "$INST" || die "install.sh's PATH candidate line changed; update tools/release-candidate.sh"
REAL="$(ls -l /opt/homebrew/bin/shotfleet /usr/local/bin/shotfleet 2>&1)"
CLEANPATH=/usr/bin:/bin:/usr/sbin:/sbin
# the installer picks the first writable of /opt/homebrew/bin, /usr/local/bin, ~/.local/bin; this Mac may have a writable
# Homebrew bin, so each run below swaps the first two candidates for a dir inside the temp HOME (nothing else is changed)
echo "-- variant A: the first candidate is a writable dir (stands for /opt/homebrew/bin)"
HA=$RUN/instA; mkdir -p "$HA/fakebrew/bin"
sed 's|for DIR in /opt/homebrew/bin /usr/local/bin |for DIR in "$HOME/fakebrew/bin" |' "$INST" > "$RUN/install-A.sh"
[ "$(diff "$INST" "$RUN/install-A.sh" | grep -c '^[<>]')" = 2 ] || die "variant A changed more than the candidate line"
echo "\$ sh install.sh   (SHOTFLEET_BASE=http://127.0.0.1:$SP/download, HOME=instA)"
OUT=$(env -i HOME="$HA" PATH="$HA/fakebrew/bin:$CLEANPATH" SHOTFLEET_BASE="http://127.0.0.1:$SP/download" sh "$RUN/install-A.sh" 2>&1); RC=$?
printf '%s\n' "$OUT" | sed 's/^/    /'; echo "    [exit $RC]"
chk "install.sh succeeds, reports the version and the directory" 0 "installed shotfleet $VERSION to $HA/fakebrew/bin"
LNK="$HA/fakebrew/bin/shotfleet"
[ -L "$LNK" ] && [ "$(readlink "$LNK")" = "$HA/Library/Application Support/shotfleet/app/shotfleet" ] && ok "the command is a link to ~/Library/Application Support/shotfleet/app/shotfleet" || fail "link wrong: $(readlink "$LNK")"
OUT=$(env -i HOME="$HA" PATH="$HA/fakebrew/bin:$CLEANPATH" shotfleet --version 2>&1); RC=$?; echo "\$ shotfleet --version  (found on the PATH) -> $OUT"
[ "$OUT" = "shotfleet $VERSION" ] && ok "shotfleet --version works from the PATH after install" || fail "shotfleet --version after install: $OUT"
if [ -n "$ID" ]; then codesign --verify --deep --strict "$HA/Library/Application Support/shotfleet/app/shotfleet" 2>&1 && ok "the installed program still verifies" || fail "installed program's signature is broken"; fi
OUT=$(env -i HOME="$HA" PATH="$HA/fakebrew/bin:$CLEANPATH" SHOTFLEET_BASE="http://127.0.0.1:$SP/download" sh "$RUN/install-A.sh" 2>&1); RC=$?
chk "re-running install.sh (an update) works over the installed copy" 0 "installed shotfleet $VERSION"
echo "-- variant B: no writable candidate, so ~/.local/bin is created"
HB=$RUN/instB; mkdir -p "$HB"
sed 's|for DIR in /opt/homebrew/bin /usr/local/bin |for DIR in |' "$INST" > "$RUN/install-B.sh"
[ "$(diff "$INST" "$RUN/install-B.sh" | grep -c '^[<>]')" = 2 ] || die "variant B changed more than the candidate line"
OUT=$(env -i HOME="$HB" PATH="$CLEANPATH" SHOTFLEET_BASE="http://127.0.0.1:$SP/download" sh "$RUN/install-B.sh" 2>&1); RC=$?
printf '%s\n' "$OUT" | sed 's/^/    /'; echo "    [exit $RC]"
chk "install.sh falls back to ~/.local/bin and tells how to put it on the PATH" 0 "installed shotfleet $VERSION to $HB/.local/bin" "add it to your PATH"
OUT=$(env -i HOME="$HB" PATH="$HB/.local/bin:$CLEANPATH" shotfleet --version 2>&1)
[ "$OUT" = "shotfleet $VERSION" ] && ok "shotfleet --version works once ~/.local/bin is on the PATH" || fail "after variant B: $OUT"
echo "-- a tampered checksum must stop the install"
HC=$RUN/instC; mkdir -p "$HC"
OUT=$(env -i HOME="$HC" PATH="$CLEANPATH" SHOTFLEET_BASE="http://127.0.0.1:$SP/download-bad" sh "$RUN/install-B.sh" 2>&1); RC=$?
chk "a wrong .sha256 is refused ('checksum mismatch')" 1 "checksum mismatch"
[ ! -e "$HC/Library/Application Support/shotfleet/app" ] && ok "nothing was installed after the mismatch" || fail "installed despite a checksum mismatch"
[ "$REAL" = "$(ls -l /opt/homebrew/bin/shotfleet /usr/local/bin/shotfleet 2>&1)" ] && ok "the real PATH locations (/opt/homebrew/bin, /usr/local/bin) were not touched" || fail "a real PATH location changed"
echo "-- tools/golive/smoke.sh against the same local server (the page checks fail by design while the site is the waitlist; only the release lines matter)"
OUT=$(sh "$ROOT/tools/golive/smoke.sh" "http://127.0.0.1:$SP" 2>&1); RC=$?
printf '%s\n' "$OUT" | grep -E 'install.sh|VERSION|archive|sha256|unpacked program|checksum logic|checks,' | sed 's/^/    /'
for want in "VERSION is $VERSION" "archive matches its .sha256" "install.sh's checksum logic accepts the served archive" "unpacked program says 'shotfleet $VERSION'" "install.sh refuses non-arm64 and checks SHA-256"; do
  printf '%s\n' "$OUT" | grep -F "$want" | grep -q '^  ok' && ok "smoke.sh: $want" || fail "smoke.sh did not pass: $want"
done
kill "$PID2" 2>/dev/null; wait "$PID2" 2>/dev/null; PID2=

# ------------------------------------------------------------------ done
echo
echo "release-candidate $VERSION: $N checks, $BAD failed"
echo "  not covered here: Apple's notarization verdict, a real Gumroad key, Gatekeeper on a browser download, a clean Mac"
[ "$BAD" = 0 ]
exit $?

: <<'__PY__'
"""Helpers for tools/release-candidate.sh: the fake Gumroad licence API and the synthetic fixtures. Stdlib only.

  rc_helper.py fake-gumroad PORTFILE PRODUCT_ID   serve on 127.0.0.1 (port 0 = any), write the port to PORTFILE
  rc_helper.py fixture DIR      two languages, one screenshot that shows the wrong one (tests/test_cli_claims.py fixture())
  rc_helper.py freetier DIR     a config with 3 languages the app does not have (the free-tier cap prints, then `run` stops before any device)
  rc_helper.py exportfx DIR     a checked run folder `export` can copy to fastlane
  rc_helper.py age FILE DAYS    make a stored licence's last check DAYS old
"""
import http.server, json, plistlib, sys, time, urllib.parse
from pathlib import Path

GOOD = "ABCDEF12-34567890-ABCDEF12-34567890"
CHARGEBACK, DISPUTED, WON = "22222222-33333333-44444444-55555555", "33333333-44444444-55555555-66666666", "44444444-55555555-66666666-77777777"
REFUNDED = "11111111-22222222-33333333-44444444"
FLAGS = {REFUNDED: {"refunded": True}, CHARGEBACK: {"chargebacked": True}, DISPUTED: {"disputed": True},
         WON: {"disputed": True, "dispute_won": True}}


class FakeGumroad:
    """POST /v2/licenses/verify, shaped like Gumroad's (what shotfleet.gumroad_verify reads): 404 + {success: false, message} for a
    key that is not this product's; 200 + {success, uses, purchase: {refunded, chargebacked, disputed, dispute_won}} otherwise;
    `uses` counts every verify unless increment_uses_count is "false". outage = a 503 from every verify."""
    def __init__(self, product_id):
        self.product_id, self.outage, self.calls = product_id, False, []
        self.uses = {k: 0 for k in (GOOD, *FLAGS)}
        self.flags = {k: dict(v) for k, v in FLAGS.items()}

    def verify(self, form):
        self.calls.append(dict(form))
        if self.outage: return 503, {"success": False, "message": "boom"}
        key = form.get("license_key")
        if key not in self.uses or form.get("product_id") != self.product_id:
            return 404, {"success": False, "message": "That license does not exist for the provided product."}
        if form.get("increment_uses_count") != "false": self.uses[key] += 1
        purchase = {"refunded": False, "chargebacked": False, "disputed": False, "dispute_won": False, **self.flags.get(key, {})}
        return 200, {"success": True, "uses": self.uses[key], "purchase": purchase}

    def control(self, form):
        if "outage" in form: self.outage = form["outage"] == "1"
        if "refund" in form: self.flags.setdefault(form["refund"], {})["refunded"] = True
        if "unrefund" in form: self.flags.setdefault(form["unrefund"], {})["refunded"] = False


def handler(fake):
    class H(http.server.BaseHTTPRequestHandler):
        def reply(self, status, body):
            data = json.dumps(body).encode()
            self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data)))
            self.end_headers(); self.wfile.write(data)

        def form(self):
            return dict(urllib.parse.parse_qsl(self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode()))

        def do_POST(self):
            if self.path == "/v2/licenses/verify": self.reply(*fake.verify(self.form()))
            elif self.path == "/_ctl": fake.control(self.form()); self.reply(200, {})
            else: self.reply(404, {"success": False})

        def do_GET(self):
            if self.path == "/_state": self.reply(200, {"uses": fake.uses, "calls": fake.calls, "outage": fake.outage})
            else: self.reply(404, {"success": False})

        def log_message(self, *a): pass
    return H


def serve(product_id, port=0, portfile=None):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler(FakeGumroad(product_id)))
    if portfile: Path(portfile).write_text(str(server.server_port))
    server.serve_forever()


def png(w=1320, h=2868):
    return b"\x89PNG\r\n\x1a\n" + b"\0\0\0\rIHDR" + w.to_bytes(4, "big") + h.to_bytes(4, "big") + bytes([8, 2]) + b"\0" * 8 + b"IDAT"


EN = {"a": "Next", "b": "Settings", "c": "Start Training"}
EL = {"a": "Επόμενο", "b": "Ρυθμίσεις", "c": "Έναρξη προπόνησης"}


def fixture(d):
    d = Path(d)
    for lp, words in (("el", EL), ("en", EN)):
        (d / "shots" / lp).mkdir(parents=True)
        (d / "shots" / lp / "1.png").write_bytes(png()); (d / "shots" / lp / "1.png.txt").write_text("\n".join(words.values()))
        (d / "locales" / lp).mkdir(parents=True)
        (d / "locales" / lp / "translation.json").write_text(json.dumps(words, ensure_ascii=False))
    (d / "shots" / "el" / "2.png").write_bytes(png()); (d / "shots" / "el" / "2.png.txt").write_text("\n".join(EN.values()))


def freetier(d):
    d = Path(d)
    (d / "App.app").mkdir(parents=True)
    (d / "App.app" / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "com.example.rc", "DTPlatformName": "iphonesimulator"}))
    (d / "flow.yaml").write_text("- launchApp\n- takeScreenshot: 01_home\n")
    for lp, words in (("en", EN), ("el", EL)):
        (d / "locales" / lp).mkdir(parents=True)
        (d / "locales" / lp / "translation.json").write_text(json.dumps(words, ensure_ascii=False))
    (d / "shotfleet.toml").write_text('[ios]\napp = "App.app"\nbundle_id = "com.example.rc"\nstrings = "locales/*/translation.json"\n'
                                      'locales = ["fr", "it", "pt"]\nruntime = "com.apple.CoreSimulator.SimRuntime.iOS-26-5"\n')


def exportfx(d):
    out = Path(d) / "out"
    (out / "raw" / "de").mkdir(parents=True)
    (out / "raw" / "de" / "01.png").write_bytes(png())
    (out / "run.json").write_text(json.dumps({"platform": "ios", "locales": {"de": {"ok": True}}}))
    (out / "check.json").write_text(json.dumps({"problems": []}))


def age(path, days):
    p = Path(path)
    p.write_text(json.dumps({**json.loads(p.read_text()), "checked": time.time() - float(days) * 86400}))


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "fake-gumroad": serve(args[1], portfile=args[0])
    else: {"fixture": fixture, "freetier": freetier, "exportfx": exportfx, "age": age}[cmd](*args)
__PY__
