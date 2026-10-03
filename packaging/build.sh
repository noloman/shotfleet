#!/bin/sh
# Build the released shotfleet: a folder with the executable, Python and the OCR helper inside (a folder starts in
# ~0.15 s; a one-file build unpacks itself on every launch, ~1.2 s, measured).
#   packaging/build.sh                      -> dist/shotfleet/ (arm64), dist/shotfleet-<version>-macos-arm64.tar.gz
# Signing and notarization run when these are set (Manu's Apple Developer account):
#   DEVELOPER_ID="Developer ID Application: Name (TEAMID)"   NOTARY_PROFILE=<xcrun notarytool store-credentials name>
set -eu
cd "$(dirname "$0")/.."
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
ARCH=$(uname -m)
rm -rf build dist && mkdir -p build
swiftc -O ocr.swift -o build/ocr
build/venv/bin/python -c "" 2>/dev/null || { rm -rf build/venv; python3 -m venv build/venv; }  # its Python may be gone (brew upgrade)
build/venv/bin/pip install --quiet --upgrade pyinstaller certifi
set -- --onedir --name shotfleet --add-binary "$PWD/build/ocr:." --add-data "$PWD/skill:skill" \
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
  xcrun notarytool submit "dist/shotfleet-$VERSION-macos-$ARCH.zip" --keychain-profile "$NOTARY_PROFILE" --wait \
    | tee build/notary.log
  grep -q "status: Accepted" build/notary.log || { echo "notarization failed: xcrun notarytool log <id> --keychain-profile $NOTARY_PROFILE" >&2; exit 1; }
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
shasum -a 256 dist/*.tar.gz
