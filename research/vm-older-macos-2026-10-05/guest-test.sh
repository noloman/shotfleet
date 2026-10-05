#!/bin/sh
# Runs INSIDE a throwaway Tart VM (Cirrus vanilla image, user admin). Tests the LIVE shotfleet release from https://shotfleet.com.
# Expects next to it: selftest.sh, samples/de/02_advanced.png, samples/ca/02_advanced.png (copied in by host-run.sh).
# Prints KEY=value result lines (prefixed "R ") plus raw output. Never touches anything outside this VM.
PATH=/usr/bin:/bin:/usr/sbin:/sbin; export PATH
IN=$(cd "$(dirname "$0")" && pwd)
W=$(mktemp -d /tmp/sfvm.XXXXXX); H=$W/home; mkdir -p "$H/tmp"
r() { echo "R $*"; }
lim() { s=$1; shift; perl -e 'alarm shift; exec @ARGV' "$s" "$@"; }   # time limit; SIGALRM exit = 142
sfenv() { s=$1; shift; env -i HOME="$H" TMPDIR="$H/tmp" USER=admin LOGNAME=admin PATH="$H/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin" LANG=en_US.UTF-8 TERM=dumb perl -e 'alarm shift; exec @ARGV' "$s" "$@"; }  # time limit; SIGALRM = 142
bad() { grep -qiE "symbol not found|dyld|library not loaded|Bad CPU type|killed: 9" "$1"; }
t0=$(date +%s)

echo "== facts"; sw_vers; uname -m; spctl --status
r "OS=$(sw_vers -productVersion) ($(sw_vers -buildVersion)) $(uname -m)"
r "CLT=$(xcode-select -p 2>/dev/null || echo none) brew=$(command -v brew || echo none) java=$( /usr/libexec/java_home >/dev/null 2>&1 && echo yes || echo none)"

echo "== install.sh (live) into a throwaway HOME"
curl -fsSL https://shotfleet.com/install.sh -o "$W/install.sh"
sfenv 120 sh "$W/install.sh" > "$W/i.out" 2>&1; IRC=$?; cat "$W/i.out"
EXE="$H/Library/Application Support/shotfleet/app/shotfleet"
[ "$IRC" = 0 ] && [ -x "$EXE" ] && r "INSTALL=PASS $(head -1 "$W/i.out")" || r "INSTALL=FAIL rc=$IRC $(tail -1 "$W/i.out")"

echo "== --version"
sfenv 90 "$EXE" --version > "$W/v.out" 2>&1; VRC=$?; cat "$W/v.out"
[ "$VRC" = 0 ] && grep -qE '^shotfleet [0-9]+\.[0-9]+\.[0-9]+' "$W/v.out" && ! bad "$W/v.out" && r "VERSION=PASS $(tail -1 "$W/v.out")" || r "VERSION=FAIL rc=$VRC $(tail -1 "$W/v.out")"

echo "== doctor (150 s limit, never --fix)"
d0=$(date +%s); sfenv 150 "$EXE" doctor > "$W/d.out" 2>&1; DRC=$?; cat "$W/d.out"
OCR=$(grep -iE "text recognition" "$W/d.out" | head -1 | cut -c1-100)
[ "$DRC" -le 2 ] && ! bad "$W/d.out" && r "DOCTOR=PASS exit $DRC in $(( $(date +%s) - d0 ))s; $OCR" || r "DOCTOR=FAIL exit $DRC; $(tail -1 "$W/d.out")"

echo "== check on two real PNGs (wger, de + ca)"
cp -R "$IN/samples" "$W/samples"
( cd "$W" && sfenv 240 "$EXE" check "$W/samples" --report "$W/report" ) > "$W/c.out" 2>&1; CRC=$?; cat "$W/c.out"
[ "$CRC" -le 1 ] && [ -f "$W/report/check.json" ] && ! bad "$W/c.out" && r "CHECK=PASS exit $CRC; $(grep -E '^checked ' "$W/c.out" | head -1 | cut -c1-90)" || r "CHECK=FAIL exit $CRC; $(tail -1 "$W/c.out")"

echo "== licence: activate with a made-up key in Gumroad's format"
KEY=$(openssl rand -hex 16 | tr a-f A-F | sed -E 's/(.{8})(.{8})(.{8})(.{8})/\1-\2-\3-\4/')
LF="$H/Library/Application Support/shotfleet/licence.json"
sfenv 60 "$EXE" activate "$KEY" > "$W/p.out" 2>&1; PRC=$?; cat "$W/p.out"
if grep -q "didn't activate" "$W/p.out" && ! grep -qi "can't reach" "$W/p.out" && [ ! -e "$LF" ] && [ "$PRC" != 0 ]; then
  r "LICENCE=PASS refused by Gumroad (exit $PRC), no licence.json; $(grep "didn't activate" "$W/p.out" | cut -c1-110)"
else r "LICENCE=FAIL exit $PRC licence.json=$([ -e "$LF" ] && echo written || echo absent); $(tail -1 "$W/p.out" | cut -c1-110)"; fi

echo "== Gatekeeper: enable assessments, quarantine downloads, run"
echo "before: $(spctl --status)"
sudo -n spctl --global-enable 2>&1 || echo admin | sudo -S spctl --global-enable 2>&1
sudo -n spctl --enable >/dev/null 2>&1
GK=$(spctl --status 2>&1); echo "after: $GK"; date; echo "-- spctl rules"; spctl --list 2>&1 | grep -iE "developer id|notarized|^[0-9]" | head -30
G=$W/gk; mkdir -p "$G"; Q="0083;$(printf %x "$(date +%s)");Safari;$(uuidgen)"
curl -fsSL https://shotfleet.com/download/shotfleet-macos-arm64.tar.gz -o "$G/shotfleet-macos-arm64.tar.gz"
curl -fsSL https://shotfleet.com/download/shotfleet-macos-arm64.pkg -o "$G/shotfleet-macos-arm64.pkg"
xattr -w com.apple.quarantine "$Q" "$G/shotfleet-macos-arm64.tar.gz"; xattr -w com.apple.quarantine "$Q" "$G/shotfleet-macos-arm64.pkg"
# Archive Utility gives every extracted file the archive's quarantine flag; do the same by hand
tar -xzf "$G/shotfleet-macos-arm64.tar.gz" -C "$G" && xattr -r -w com.apple.quarantine "$Q" "$G/shotfleet"
echo "quarantine on program: $(xattr -p com.apple.quarantine "$G/shotfleet/shotfleet" 2>&1)"
spctl -a -vvv -t exec "$G/shotfleet/shotfleet" > "$W/g1.out" 2>&1; cat "$W/g1.out"
sfenv 90 "$G/shotfleet/shotfleet" --version > "$W/g2.out" 2>&1; G2=$?; cat "$W/g2.out"
[ "$G2" = 0 ] && grep -qE '^shotfleet [0-9]' "$W/g2.out" && r "GK_TARBALL=PASS quarantined program ran: $(tail -1 "$W/g2.out"); spctl: $(tr '\n' ' ' < "$W/g1.out" | cut -c1-120)" \
  || r "GK_TARBALL=FAIL rc=$G2 $(tail -1 "$W/g2.out"); spctl: $(tr '\n' ' ' < "$W/g1.out" | cut -c1-120)"
spctl -a -vvv -t install "$G/shotfleet-macos-arm64.pkg" > "$W/g3.out" 2>&1; G3=$?; cat "$W/g3.out"
sudo -n installer -pkg "$G/shotfleet-macos-arm64.pkg" -target / > "$W/g4.out" 2>&1; G4=$?; cat "$W/g4.out"
lim 90 /usr/local/lib/shotfleet/shotfleet --version > "$W/g5.out" 2>&1; G5=$?; cat "$W/g5.out"
[ "$G3" = 0 ] && [ "$G4" = 0 ] && [ "$G5" = 0 ] && r "GK_PKG=PASS spctl: $(tr '\n' ' ' < "$W/g3.out" | cut -c1-100); installed; $(tail -1 "$W/g5.out")" \
  || r "GK_PKG=FAIL spctl rc=$G3 installer rc=$G4 run rc=$G5; $(tr '\n' ' ' < "$W/g3.out" | cut -c1-100)"
r "GATEKEEPER_STATUS=$GK"
echo "-- syspolicy_check on the quarantined program"; syspolicy_check distribution "$G/shotfleet/shotfleet" 2>&1 | grep -E "Error|passed|failed" | head -5
echo "-- log of syspolicyd for the pkg (last 2 min)"; log show --last 2m --predicate 'process == "syspolicyd"' --style compact 2>/dev/null | grep -iE "shotfleet|reject|deny|ticket|notar" | tail -15

echo "== cross-check: tools/selftest.sh --download --licence-probe"
lim 400 sh "$IN/selftest.sh" --download --licence-probe > "$W/s.out" 2>&1; cat "$W/s.out"
r "SELFTEST=$(grep -E '^===== shotfleet selftest' "$W/s.out" | head -1)"
r "TOTAL=$(( $(date +%s) - t0 ))s"
rm -rf "$W"
