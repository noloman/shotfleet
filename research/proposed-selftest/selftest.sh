#!/bin/sh
# shotfleet self-test: does the release start on THIS Mac? (PROPOSED, research/proposed-selftest/, not part of the product)
#
#   sh selftest.sh --tarball shotfleet-macos-arm64.tar.gz     # a file you already have: nothing is downloaded
#   sh selftest.sh --download                                 # fetch the release from shotfleet.com (about 10 MB) and check its sha256
#   sh selftest.sh --folder /path/to/unpacked/shotfleet       # an already unpacked folder (keeps its quarantine flag, see below)
#
# Options:
#   --base URL        where --download looks (default https://shotfleet.com/download, as install.sh)
#   --quarantine      mark the program as downloaded from a browser (the flag Gatekeeper judges), then run it
#   --licence-probe   also run `shotfleet activate` with a made-up key: sends that key to Gumroad's verify endpoint (one HTTPS request,
#                     nothing is stored), proves the packaged program can reach and trust Gumroad. Off by default.
#   --hide-tools      (for a Mac that has Homebrew, Java, Android tools) hide /opt/homebrew, /usr/local, /Library/Java and the
#                     Android, Maestro and shotfleet folders of your home from the program with sandbox-exec: a stand-in for a clean Mac
#   --keep            do not delete the throwaway folder at the end (its path is printed)
#
# What it does: makes a throwaway HOME, installs the program there the way install.sh does (but puts NO link on your PATH and touches
# nothing outside the throwaway folder), runs `shotfleet --version`, `shotfleet doctor` (never --fix, 150 s limit) and `shotfleet check`
# on two screenshots it draws itself, and prints ONE result block to paste back. It does not write anywhere else, install anything,
# sign in or change settings. `doctor` asks shotfleet.com once whether a newer version exists (a read), as it always does.
# Needs only what every Mac has: sh, curl (only with --download), tar, shasum, perl, osascript, sips, sw_vers.
# Exit 0 = PASS, 1 = FAIL, 2 = wrong usage.
REAL_PATH=$PATH
PATH=/usr/bin:/bin:/usr/sbin:/sbin; export PATH
MODE=; SRC=; BASE=https://shotfleet.com/download; QUAR=0; PROBE=0; HIDE=0; KEEP=0
usage() { sed -n '2,/^# Exit 0/p' "$0" | sed 's/^# \{0,1\}//'; }
while [ $# -gt 0 ]; do
  case "$1" in
    --tarball) MODE=tarball; SRC=${2:?--tarball needs a file}; shift ;;
    --folder) MODE=folder; SRC=${2:?--folder needs a folder}; shift ;;
    --download) MODE=download ;;
    --base) BASE=${2:?--base needs a URL}; shift ;;
    --quarantine) QUAR=1 ;;
    --licence-probe|--license-probe) PROBE=1 ;;
    --hide-tools) HIDE=1 ;;
    --keep) KEEP=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
  esac
  shift
done
if [ -z "$MODE" ]; then
  HERE=$(cd "$(dirname "$0")" && pwd)
  for f in "$HERE"/shotfleet-*macos-arm64.tar.gz "$PWD"/shotfleet-*macos-arm64.tar.gz; do [ -f "$f" ] && { MODE=tarball; SRC=$f; break; }; done
fi
[ -n "$MODE" ] || { echo "nothing to test: pass --tarball FILE, --folder DIR or --download (see --help)" >&2; exit 2; }
[ "$(uname -s)" = Darwin ] || { echo "this test is for macOS only" >&2; exit 2; }

W=$(mktemp -d /tmp/shotfleet-selftest.XXXXXX) || exit 2
cleanup() { [ "$KEEP" = 1 ] && echo "kept: $W" || rm -rf "$W"; }
trap cleanup EXIT
trap 'exit 130' INT TERM
H=$W/home; mkdir -p "$H/tmp"
APP="$H/Library/Application Support/shotfleet/app"
LOG=$W/log; : > "$LOG"
say() { echo "$*" | tee -a "$LOG"; }

# --- facts about this Mac (before anything runs) ---
OSV=$(sw_vers -productVersion); OSB=$(sw_vers -buildVersion); ARCH=$(uname -m)
MODEL=$(sysctl -n hw.model 2>/dev/null); ARM64=$(sysctl -n hw.optional.arm64 2>/dev/null)
RAM=$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))
GK=$(spctl --status 2>&1 | head -1)
have() { PATH=$REAL_PATH command -v "$1" >/dev/null 2>&1 && echo yes || echo no; }
TOOLS="brew=$(have brew) java=$(have java) maestro=$(have maestro) xcodebuild=$(have xcodebuild) python3=$(have python3)"
XC=$(xcode-select -p 2>/dev/null || echo none)

# --- the program, in a throwaway HOME, the way install.sh puts it ---
STEP_INSTALL=FAIL; INSTALL_NOTE=
mkdir -p "$(dirname "$APP")"
case "$MODE" in
  folder)
    if [ -f "$SRC/shotfleet" ]; then ditto "$SRC" "$APP" && STEP_INSTALL=ok
    elif [ -f "$SRC/shotfleet/shotfleet" ]; then ditto "$SRC/shotfleet" "$APP" && STEP_INSTALL=ok
    else INSTALL_NOTE="no shotfleet program in $SRC"; fi ;;
  tarball|download)
    T=$W/shotfleet.tar.gz
    if [ "$MODE" = download ]; then
      if curl -fsSL "$BASE/shotfleet-macos-arm64.tar.gz" -o "$T" && curl -fsSL "$BASE/shotfleet-macos-arm64.tar.gz.sha256" -o "$W/sum"; then
        [ "$(shasum -a 256 "$T" | cut -d' ' -f1)" = "$(cut -d' ' -f1 "$W/sum")" ] || { INSTALL_NOTE="checksum mismatch"; T=; }
      else INSTALL_NOTE="download failed"; T=; fi
    else
      [ -f "$SRC" ] && cp "$SRC" "$T" || { INSTALL_NOTE="no such file: $SRC"; T=; }
      # a browser download carries the quarantine flag; report it, it is what Gatekeeper judges
      xattr -p com.apple.quarantine "$SRC" >/dev/null 2>&1 && INSTALL_NOTE="the tarball you gave carries the quarantine flag"
    fi
    if [ -n "$T" ] && mkdir "$W/x" && tar -xzf "$T" -C "$W/x" 2>"$W/tar.err" && [ -f "$W/x/shotfleet/shotfleet" ]; then
      mv "$W/x/shotfleet" "$APP" && STEP_INSTALL=ok
    elif [ -z "$INSTALL_NOTE" ] || [ -n "$T" ]; then INSTALL_NOTE="$INSTALL_NOTE; cannot unpack: $(head -1 "$W/tar.err" 2>/dev/null)"; fi ;;
esac
EXE=$APP/shotfleet
[ "$STEP_INSTALL" = ok ] && [ -x "$EXE" ] || STEP_INSTALL=FAIL
if [ "$STEP_INSTALL" = ok ] && [ "$QUAR" = 1 ]; then xattr -w com.apple.quarantine "0081;00000000;Safari;" "$EXE"; fi
QFLAG=$(xattr -p com.apple.quarantine "$EXE" >/dev/null 2>&1 && echo yes || echo no)

# --- running it: empty environment, throwaway home, optional hiding of this Mac's tools ---
SB=
if [ "$HIDE" = 1 ]; then
  RH=$(eval echo "~$(id -un)")
  cat > "$W/hide.sb" <<EOF
(version 1)
(allow default)
(deny file-read* file-write*
  (subpath "/opt/homebrew") (subpath "/usr/local") (subpath "/Library/Java")
  (subpath "$RH/Library/Android") (subpath "$RH/.android") (subpath "$RH/.shotfleet") (subpath "$RH/.maestro")
  (subpath "$RH/.sdkman") (subpath "$RH/.gradle") (subpath "$RH/Library/Application Support/shotfleet"))
EOF
  SB="sandbox-exec -f $W/hide.sb"
fi
run() {  # run SECONDS cmd args...: clean environment, time limit, optional sandbox
  s=$1; shift
  env -i HOME="$H" SHOTFLEET_HOME="$H/.shotfleet" ANDROID_HOME="$H/android" TMPDIR="$H/tmp" USER="$(id -un)" LOGNAME="$(id -un)" \
    PATH=/usr/bin:/bin:/usr/sbin:/sbin LANG=en_US.UTF-8 TERM=dumb $SB perl -e 'alarm shift; exec @ARGV' "$s" "$@"
}
bad() { grep -qiE "symbol not found|dyld|library not loaded|Bad CPU type|killed: 9" "$1"; }

V=FAIL; D=FAIL; C=FAIL; P=skipped; VOUT=; DRC=-; CRC=-
if [ "$STEP_INSTALL" = ok ]; then
  say "== shotfleet --version"
  run 90 "$EXE" --version >"$W/v.out" 2>&1 </dev/null; VRC=$?; cat "$W/v.out" | tee -a "$LOG"
  VOUT=$(tail -1 "$W/v.out")
  if [ "$VRC" = 0 ] && echo "$VOUT" | grep -qE '^shotfleet [0-9]+\.[0-9]+\.[0-9]+'; then V=ok; fi

  if [ "$V" = ok ]; then
    say "== shotfleet doctor (never --fix; exit 2 means 'not ready yet', which is expected on a clean Mac)"
    run 150 "$EXE" doctor >"$W/d.out" 2>&1 </dev/null; DRC=$?; tail -25 "$W/d.out" | tee -a "$LOG"
    if [ "$DRC" -le 2 ] && ! bad "$W/d.out"; then D=ok; fi

    say "== shotfleet check on two screenshots drawn here"
    mkdir -p "$W/samples/en" "$W/samples/de"
    cat > "$W/draw.js" <<'EOF'
ObjC.import("AppKit"); ObjC.import("CoreGraphics");
function make(path, lines) {
  var w = 1290, h = 2796;
  var rep = $.NSBitmapImageRep.alloc.initWithBitmapDataPlanesPixelsWidePixelsHighBitsPerSampleSamplesPerPixelHasAlphaIsPlanarColorSpaceNameBytesPerRowBitsPerPixel(null, w, h, 8, 4, true, false, $.NSDeviceRGBColorSpace, 0, 0);
  var ctx = $.NSGraphicsContext.graphicsContextWithBitmapImageRep(rep);
  $.NSGraphicsContext.setCurrentContext(ctx);
  var cg = ctx.CGContext; $.CGContextSetRGBFillColor(cg, 1, 1, 1, 1); $.CGContextFillRect(cg, $.CGRectMake(0, 0, w, h));
  $.CGContextSetRGBFillColor(cg, 0.2, 0.5, 0.95, 1); $.CGContextFillRect(cg, $.CGRectMake(0, h - 300, w, 300));
  for (var j = 0; j < 7; j++) { $.CGContextSetRGBFillColor(cg, 0.86, 0.9, 0.97, 1); $.CGContextFillRect(cg, $.CGRectMake(40, h - 700 - j * 300, w - 80, 250)); }
  var attrs = $.NSMutableDictionary.alloc.init;
  attrs.setObjectForKey($.NSFont.boldSystemFontOfSize(62), $.NSFontAttributeName);
  for (var i = 0; i < lines.length; i++)
    $.NSString.stringWithString(lines[i]).drawAtPointWithAttributes($.NSMakePoint(80, h - 650 - i * 300), attrs);
  rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $.NSMutableDictionary.alloc.init).writeToFileAtomically(path, true);
}
var a = $.NSProcessInfo.processInfo.arguments, dir = ObjC.unwrap(a.objectAtIndex(a.count - 1));
make(dir + "/en/01_home.png", ["Welcome back", "Your settings and privacy", "Notifications are on", "Search for workouts", "Your plan renews on Friday", "Share progress with friends"]);
make(dir + "/de/01_home.png", ["Willkommen zurueck", "Deine Einstellungen und Datenschutz", "Benachrichtigungen sind aktiv", "Suche nach Trainings", "Dein Plan verlaengert sich am Freitag", "Teile Fortschritte mit Freunden"]);
EOF
    osascript -l JavaScript "$W/draw.js" "$W/samples" >"$W/draw.out" 2>&1
    # the stores reject PNGs with an alpha channel; a trip through JPEG drops it (sips has no direct switch)
    for f in "$W/samples/en/01_home.png" "$W/samples/de/01_home.png"; do
      sips -s format jpeg -s formatOptions 95 "$f" --out "$f.jpg" >/dev/null 2>&1 && sips -s format png "$f.jpg" --out "$f" >/dev/null 2>&1; rm -f "$f.jpg"
    done
    if [ -s "$W/samples/en/01_home.png" ] && [ -s "$W/samples/de/01_home.png" ]; then
      say "drawn: $(sips -g pixelWidth -g pixelHeight "$W/samples/en/01_home.png" 2>/dev/null | awk '/pixel/ {printf "%s ", $2}')pixels, 2 files"
      ( cd "$W" && run 240 "$EXE" check "$W/samples" --report "$W/report" ) >"$W/c.out" 2>&1 </dev/null; CRC=$?
      tail -25 "$W/c.out" | tee -a "$LOG"
      # exit 0 = no problems, 1 = problems reported (a report was produced): both mean `check` ran to the end
      if [ "$CRC" -le 1 ] && ! bad "$W/c.out" && [ -f "$W/report/check.json" ]; then C=ok; fi
    else
      C=skipped; say "could not draw the screenshots: $(head -1 "$W/draw.out")"
    fi

    if [ "$PROBE" = 1 ]; then
      say "== licence probe: shotfleet activate with a made-up key"
      run 60 "$EXE" activate 00000000-00000000-00000000-00000000 >"$W/p.out" 2>&1 </dev/null; tail -3 "$W/p.out" | tee -a "$LOG"
      if grep -q "didn't activate" "$W/p.out" && ! grep -qi "can't reach" "$W/p.out"; then P=ok; else P=FAIL; fi
    fi
  fi
fi

RES=PASS
[ "$STEP_INSTALL" = ok ] && [ "$V" = ok ] && [ "$D" = ok ] && [ "$C" != FAIL ] && [ "$P" != FAIL ] || RES=FAIL
[ "$C" = skipped ] && RES="$RES (check was skipped)"
OCR=$(grep -E "^(ok|MISSING|WARN)[ ]+text recognition" "$W/d.out" 2>/dev/null | head -1 | cut -c1-110)
IOS=$(grep -iE "ios runtime|simulator runtime" "$W/d.out" 2>/dev/null | head -1 | cut -c1-110)
N=$(grep -E "^checked " "$W/c.out" 2>/dev/null | head -1 | cut -c1-90)
echo
echo "===== shotfleet selftest: $RES ====="
echo "macOS $OSV ($OSB), $ARCH, hw.optional.arm64=$ARM64, $MODEL, ${RAM} GB"
echo "Gatekeeper: $GK   quarantine flag on the program: $QFLAG   hidden tools: $([ "$HIDE" = 1 ] && echo yes || echo no)"
echo "your own PATH had: $TOOLS; Xcode path: $XC"
echo "source: $MODE   $INSTALL_NOTE"
echo "install into a throwaway HOME: $STEP_INSTALL"
echo "--version: $V   ${VOUT}"
echo "doctor: $D (exit $DRC)   $OCR"
[ -n "$IOS" ] && echo "doctor, iOS: $IOS"
echo "check on 2 drawn screenshots: $C (exit $CRC)   $N"
echo "licence probe: $P"
echo "paste everything between the two ===== lines into your reply (no file names or user name are printed)"
echo "===== end ====="
[ "${RES%% *}" = PASS ]
