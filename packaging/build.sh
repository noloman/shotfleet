#!/bin/sh
# Build the released shotfleet: a folder with the executable, Python and the OCR helper inside (a folder starts in
# ~0.15 s; a one-file build unpacks itself on every launch, ~1.2 s, measured).
#   packaging/build.sh                      -> dist/shotfleet/ (arm64), dist/shotfleet-<version>-macos-arm64.tar.gz
# Signing and notarization run when these are set (Manu's Apple Developer account):
#   DEVELOPER_ID="Developer ID Application: Name (TEAMID)"   NOTARY_PROFILE=ShotfleetNotary
# Which macOS the build runs on (research/limits-platform-reach-2026-10-05.md): the Swift OCR helper targets macOS ${MACOS_MIN:-13.0}
# (Vision's newer text models start there). The Python is the recorded one, python-build-standalone ${PINNED_PYTHON:-3.14.2} from uv
# (`uv python install 3.14.2`), built for macOS 11, so the program runs on macOS 13 and newer; a Homebrew Python is built for the macOS it
# was built on (27.0 measured), so the whole program would need that macOS, and it is refused. PYTHON=<interpreter> names another copy
# of that same version. The build installs ONLY packaging/requirements-build.txt (exact versions with hashes: PyInstaller, its hooks
# and dependencies, certifi) with `pip --require-hashes`, so two builds use the same inputs. Offline, point pip at a folder of those wheels:
#   PIP_NO_INDEX=1 PIP_FIND_LINKS=<folder of wheels> packaging/build.sh
# The last lines say which macOS the build needs.
set -eu
cd "$(dirname "$0")/.."
if [ -n "${DEVELOPER_ID:-}" ] && [ -n "${NOTARY_PROFILE:-}" ]; then packaging/notary-check.sh; fi  # minutes before the submit would find out
notary_failed() {  # $1: the notarytool log; name the submission id only when Apple gave one
  ID=$(sed -n 's/^ *id: //p' "$1" | head -1)
  if [ -n "$ID" ]; then echo "notarization failed: xcrun notarytool log $ID --keychain-profile $NOTARY_PROFILE" >&2
  else echo "notarization failed before Apple gave a submission id (notarytool's message is above; check the profile: packaging/notary-check.sh)" >&2; fi
  exit 1
}
PINNED_PYTHON=${PINNED_PYTHON:-3.14.2}; MINOS_MAX=${PYTHON_MINOS_MAX:-11}
PYTHON=${PYTHON:-$(uv python find "$PINNED_PYTHON" --managed-python 2>/dev/null || true)}
[ -n "$PYTHON" ] && [ -x "$PYTHON" ] || { echo "build: no standalone Python $PINNED_PYTHON (run: uv python install $PINNED_PYTHON, or set PYTHON=<interpreter>)" >&2; exit 1; }
GOT=$("$PYTHON" -c 'import sys;print("%d.%d.%d" % sys.version_info[:3])')
[ "$GOT" = "$PINNED_PYTHON" ] || { echo "build: $PYTHON is Python $GOT, the recorded build Python is $PINNED_PYTHON (change PINNED_PYTHON and requirements-build.txt on purpose, not by accident)" >&2; exit 1; }
PYMINOS=$(mktemp -d); cp "$(python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "$PYTHON")" "$PYMINOS/python"  # macho-minos reads regular files only
python3 tools/macho-minos.py "$PYMINOS" --max "$MINOS_MAX" >/dev/null 2>&1 || { rm -rf "$PYMINOS"; echo "build: $PYTHON needs a newer macOS than $MINOS_MAX.0 (a Homebrew Python?): the program would need that macOS too" >&2; exit 1; }
rm -rf "$PYMINOS"
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
ARCH=$(uname -m)
rm -rf build dist && mkdir -p build
swiftc -O -target "$ARCH-apple-macos${MACOS_MIN:-13.0}" ocr.swift -o build/ocr
"$PYTHON" -m venv build/venv  # fresh every build (build/ was just removed)
build/venv/bin/python -m pip install --quiet --disable-pip-version-check --only-binary=:all: --require-hashes -r packaging/requirements-build.txt \
  || { echo "build: installing packaging/requirements-build.txt failed (a hash mismatch means the file is not the recorded one: do not build; see pip's message above)" >&2; exit 1; }
# The release date the licence's year of updates is measured against (shotfleet.py baked_release_date): the build day, in UTC.
# A build is published days after it is made, never before, so this errs in the buyer's favour. It goes into a module that PyInstaller
# freezes into the program's code (not a loose file in _internal, which anyone could delete).
printf 'RELEASE_DATE = "%s"\n' "$(date -u +%Y-%m-%d)" > build/_release.py
set -- --onedir --name shotfleet --add-binary "$PWD/build/ocr:." --add-data "$PWD/skill:skill" --paths "$PWD/build" --hidden-import _release \
  --distpath dist --workpath build/pyi --specpath build --noconfirm --log-level WARN
if [ -n "${DEVELOPER_ID:-}" ]; then  # PyInstaller signs the bundled pieces too, with hardened-runtime entitlements
  codesign --force --options runtime --timestamp --sign "$DEVELOPER_ID" build/ocr
  set -- "$@" --codesign-identity "$DEVELOPER_ID" --osx-entitlements-file "$PWD/packaging/entitlements.plist"
fi
build/venv/bin/pyinstaller "$@" shotfleet.py
if [ -n "${DEVELOPER_ID:-}" ]; then
  # Re-sign every binary in the folder, deepest first (PyInstaller's signing leaves Homebrew's Python framework
  # with a signature Apple's notary rejects), then the executable with the hardened-runtime entitlements.
  find dist/shotfleet -type f | while read -r f; do file -b "$f" | grep -q Mach-O && echo "$f"; done \
    | awk '{ print gsub("/", "/"), $0 }' | sort -rn | cut -d' ' -f2- | while read -r f; do
      codesign --force --options runtime --timestamp --sign "$DEVELOPER_ID" "$f"
    done
  find dist/shotfleet -name "*.framework" -type d | while read -r fw; do
    codesign --force --options runtime --timestamp --sign "$DEVELOPER_ID" "$fw"
  done
  codesign --force --options runtime --timestamp --entitlements packaging/entitlements.plist \
    --sign "$DEVELOPER_ID" dist/shotfleet/shotfleet
  codesign --verify --deep --strict dist/shotfleet/shotfleet
fi
tar -C dist -czf "dist/shotfleet-$VERSION-macos-$ARCH.tar.gz" shotfleet
if [ -n "${DEVELOPER_ID:-}" ] && [ -n "${NOTARY_PROFILE:-}" ]; then
  (cd dist && ditto -c -k --keepParent shotfleet "shotfleet-$VERSION-macos-$ARCH.zip")
  packaging/notary-check.sh  # again: the build took minutes and the screen may have locked since
  (set -o pipefail; xcrun notarytool submit "dist/shotfleet-$VERSION-macos-$ARCH.zip" --keychain-profile "$NOTARY_PROFILE" --wait \
    | tee build/notary.log) || notary_failed build/notary.log  # pipefail only here: tee must not hide notarytool's exit status
  grep -q "status: Accepted" build/notary.log || notary_failed build/notary.log
  # Don't trust the verdict alone: unpack the tarball we will ship, mark it as downloaded (quarantine) and ask Gatekeeper.
  CHECK=$(mktemp -d); tar -C "$CHECK" -xzf "dist/shotfleet-$VERSION-macos-$ARCH.tar.gz"
  xattr -w com.apple.quarantine "0081;00000000;Safari;" "$CHECK/shotfleet/shotfleet"
  # spctl cannot assess a bare executable ("does not seem to be an app", no source line), so run it: a quarantined copy that
  # is not notarized hangs and is killed, a notarized one prints its version (first run looks the ticket up online, ~10 s).
  perl -e 'alarm 90; exec @ARGV' "$CHECK/shotfleet/shotfleet" --version 2>&1 | tee build/spctl.log
  grep -q "^shotfleet $VERSION\$" build/spctl.log || { rm -rf "$CHECK"; echo "a quarantined copy of the shipped build does not run (build/spctl.log): do not publish" >&2; exit 1; }
  rm -rf "$CHECK"
fi
# The installer package (no quarantine flag, so no Gatekeeper check at run time): needs the Developer ID Installer certificate.
if [ -n "${INSTALLER_ID:-}" ]; then packaging/pkg.sh; fi
python3 tools/macho-minos.py dist/shotfleet || true  # informational: the oldest macOS this build runs on
shasum -a 256 dist/*.tar.gz
