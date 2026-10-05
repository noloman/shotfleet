#!/bin/sh
# Verify a built shotfleet release. READ-ONLY: it unpacks and runs copies in a temp dir and changes nothing it was given.
#   tools/verify-release.sh [options] <unpacked build folder | .tar.gz | .pkg> ...
# Options:
#   --manifest <file>        check each tarball/pkg against the manifest (packaging/publish.sh --make-manifest writes it); sets the expected version
#   --expect-version <X.Y.Z> the version `--version` must print (default: the manifest's, else any X.Y.Z)
#   --max-macos <N>          fail when some Mach-O file needs a newer macOS than N (default 13)
#   --team <ID>              Apple team id the files must be signed with (default 2357A78TMR)
#   --no-run                 skip the quarantined `--version` run (it asks Apple's servers on the first run, ~10 s)
# For a folder or tarball: every Mach-O file verifies (codesign --verify --strict; the program also --deep) with the team id, the program
# has the hardened runtime flag, a quarantined copy prints its version, tools/macho-minos.py stays at or below the maximum.
# For a .pkg: its signature (Developer ID Installer, the team), spctl -t install and xcrun stapler validate.
# Ends with PASS or FAIL; exit 1 on any FAIL.
PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH; export PATH
HERE=$(cd "$(dirname "$0")" && pwd)
MANIFEST=; EXPECT=; MAX=13; TEAM=2357A78TMR; RUN=1; TARGETS=
usage() { sed -n '2,/^PATH=/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; }
while [ $# -gt 0 ]; do
  case "$1" in
    --manifest) MANIFEST=${2:?--manifest needs a file}; shift ;;
    --expect-version) EXPECT=${2:?--expect-version needs a version}; shift ;;
    --max-macos) MAX=${2:?--max-macos needs a number}; shift ;;
    --team) TEAM=${2:?--team needs an id}; shift ;;
    --no-run) RUN=0 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
    *) TARGETS="$TARGETS
$1" ;;
  esac
  shift
done
[ -n "$TARGETS" ] || { echo "usage: tools/verify-release.sh [options] <folder | .tar.gz | .pkg> ... (see --help)" >&2; exit 2; }
if [ -n "$MANIFEST" ]; then
  [ -f "$MANIFEST" ] || { echo "no such manifest: $MANIFEST" >&2; exit 2; }
  [ -n "$EXPECT" ] || EXPECT=$(awk '$1 == "version" { print $2 }' "$MANIFEST")
fi
W=$(mktemp -d) && trap 'rm -rf "$W"' EXIT
N=0; BAD=0
ok() { N=$((N + 1)); echo "  ok    $*"; }
skip() { echo "  SKIP  $*"; }
fail() { N=$((N + 1)); BAD=$((BAD + 1)); echo "  FAIL  $*"; }
sha256() { shasum -a 256 "$1" | cut -d' ' -f1; }

manifest_check() {  # <file>: size and sha256 against the manifest line with the same name
  if [ -z "$MANIFEST" ]; then skip "no --manifest: the file's hash is not checked"; return; fi
  name=$(basename "$1"); line=$(awk -v n="$name" '$1 == "file" && $4 == n { print $2, $3 }' "$MANIFEST")
  if [ -z "$line" ]; then fail "$name is not in the manifest"; return; fi
  if [ "$(wc -c < "$1" | tr -d ' ')" = "${line#* }" ] && [ "$(sha256 "$1")" = "${line% *}" ]; then ok "$name matches the manifest (${line#* } bytes, sha256 ${line%% *})"
  else fail "$name does NOT match the manifest: it is not the tested file"; fi
}

check_folder() {  # <folder holding the `shotfleet` executable>
  d=$1; exe=$d/shotfleet
  [ -f "$exe" ] || { fail "$d has no shotfleet executable"; return; }
  machos=$W/machos; : > "$machos"
  find "$d" -type f | while read -r f; do file -b "$f" | grep -q Mach-O && echo "$f"; done > "$machos"
  total=$(wc -l < "$machos" | tr -d ' '); bad_sig=0; bad_team=0
  while read -r f; do
    codesign --verify --strict "$f" >/dev/null 2>&1 || { bad_sig=$((bad_sig + 1)); echo "        not valid: $f"; }
    codesign -dvv "$f" 2>&1 | grep -q "^TeamIdentifier=$TEAM\$" || { bad_team=$((bad_team + 1)); echo "        not team $TEAM: $f"; }
  done < "$machos"
  if [ "$total" -gt 0 ] && [ "$bad_sig" = 0 ]; then ok "all $total Mach-O files pass codesign --verify --strict"; else fail "$bad_sig of $total Mach-O files fail codesign --verify --strict"; fi
  if [ "$total" -gt 0 ] && [ "$bad_team" = 0 ]; then ok "all $total Mach-O files carry team id $TEAM"; else fail "$bad_team of $total Mach-O files lack team id $TEAM"; fi
  if codesign --verify --deep --strict "$exe" >"$W/cs.out" 2>&1; then ok "codesign --verify --deep --strict shotfleet"; else fail "codesign --verify --deep --strict shotfleet: $(head -1 "$W/cs.out")"; fi
  info=$(codesign -dvv "$exe" 2>&1)
  if echo "$info" | grep -q 'flags=.*runtime'; then ok "shotfleet has the hardened runtime flag"; else fail "shotfleet lacks the hardened runtime flag"; fi
  if echo "$info" | grep -q '^Authority=Developer ID Application'; then ok "signed with a Developer ID Application certificate"; else fail "not signed with a Developer ID Application certificate"; fi
  if python3 "$HERE/macho-minos.py" "$d" --max "$MAX" >"$W/minos.out" 2>&1; then ok "build $(grep -o 'needs macOS [0-9.]* or newer' "$W/minos.out" | tail -1) (maximum allowed: macOS $MAX)"
  else fail "needs a newer macOS than $MAX: $(grep -v '^this build' "$W/minos.out" | tail -2 | tr '\n' ';' | tr -s ' ')"; fi
  if [ "$RUN" = 1 ]; then
    q=$W/quarantined; rm -rf "$q"; ditto "$d" "$q" && xattr -w com.apple.quarantine "0081;00000000;Safari;" "$q/shotfleet"
    got=$(perl -e 'alarm 90; exec @ARGV' "$q/shotfleet" --version 2>&1 </dev/null | tail -1)
    if [ -n "$EXPECT" ]; then want="shotfleet $EXPECT"; else want=$(echo "$got" | grep -E '^shotfleet [0-9]+\.[0-9]+\.[0-9]+$' || echo "shotfleet X.Y.Z"); fi
    if [ "$got" = "$want" ]; then ok "a quarantined copy runs: '$got'"; else fail "a quarantined copy printed '${got:-nothing}' (wanted '$want'): not notarized, or it hangs"; fi
  else skip "quarantined --version run (--no-run)"; fi
}

IFS='
'  # one target per line, so paths may hold spaces
for t in $TARGETS; do
  echo "== $t =="
  if [ -d "$t" ]; then
    skip "a folder has no hash to check against the manifest"
    if [ -f "$t/shotfleet" ]; then check_folder "$t"; elif [ -f "$t/shotfleet/shotfleet" ]; then check_folder "$t/shotfleet"; else fail "no shotfleet executable in $t"; fi
  elif [ -f "$t" ]; then
    case "$t" in
      *.tar.gz|*.tgz)
        manifest_check "$t"; rm -rf "$W/x"; mkdir "$W/x"
        if tar -xzf "$t" -C "$W/x" 2>"$W/tar.err"; then
          if [ -f "$W/x/shotfleet/shotfleet" ]; then check_folder "$W/x/shotfleet"; else fail "the tarball has no shotfleet/shotfleet"; fi
        else fail "cannot unpack: $(head -1 "$W/tar.err")"; fi ;;
      *.pkg)
        manifest_check "$t"
        sig=$(pkgutil --check-signature "$t" 2>&1)
        if echo "$sig" | grep -q "Developer ID Installer" && echo "$sig" | grep -q "($TEAM)"; then ok "pkg signed by Developer ID Installer ($TEAM)"; else fail "pkg is not signed by a Developer ID Installer certificate of team $TEAM"; fi
        sp=$(spctl -a -vv -t install "$t" 2>&1)
        if echo "$sp" | grep -q ': accepted' && echo "$sp" | grep -q 'source=Notarized Developer ID'; then ok "spctl -t install: accepted, Notarized Developer ID"; else fail "spctl -t install: $(echo "$sp" | tr '\n' ' ' | cut -c1-120)"; fi
        if xcrun stapler validate "$t" >"$W/st.out" 2>&1; then ok "stapler validate: ticket stapled"; else fail "stapler validate: $(tail -1 "$W/st.out")"; fi ;;
      *) fail "not a folder, .tar.gz or .pkg: $t" ;;
    esac
  else fail "no such file or folder: $t"; fi
done
if [ "$BAD" = 0 ]; then echo "PASS: $N checks, 0 failed"; exit 0; fi
echo "FAIL: $N checks, $BAD failed"; exit 1
