#!/bin/sh
# Build the released shotfleet: one executable with Python and the OCR helper inside.
#   packaging/build.sh                      -> dist/shotfleet (arm64), dist/shotfleet-<version>-macos-arm64.tar.gz
# Signing and notarization run when these are set (Manu's Apple Developer account):
#   DEVELOPER_ID="Developer ID Application: Name (TEAMID)"   NOTARY_PROFILE=<xcrun notarytool store-credentials name>
set -eu
cd "$(dirname "$0")/.."
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
ARCH=$(uname -m)
rm -rf build dist && mkdir -p build
swiftc -O ocr.swift -o build/ocr
[ -d build/venv ] || python3 -m venv build/venv
build/venv/bin/pip install --quiet --upgrade pyinstaller
SIGN=""
if [ -n "${DEVELOPER_ID:-}" ]; then  # PyInstaller signs the bundled pieces too, with hardened-runtime entitlements
  codesign --force --options runtime --timestamp --sign "$DEVELOPER_ID" build/ocr
  SIGN="--codesign-identity $DEVELOPER_ID --osx-entitlements-file packaging/entitlements.plist"
fi
build/venv/bin/pyinstaller --onefile --name shotfleet --add-binary "$PWD/build/ocr:." $SIGN \
  --distpath dist --workpath build/pyi --specpath build --noconfirm --log-level WARN shotfleet.py
tar -C dist -czf "dist/shotfleet-$VERSION-macos-$ARCH.tar.gz" shotfleet
if [ -n "${DEVELOPER_ID:-}" ] && [ -n "${NOTARY_PROFILE:-}" ]; then
  (cd dist && ditto -c -k shotfleet "shotfleet-$VERSION-macos-$ARCH.zip")
  xcrun notarytool submit "dist/shotfleet-$VERSION-macos-$ARCH.zip" --keychain-profile "$NOTARY_PROFILE" --wait
fi
shasum -a 256 dist/*.tar.gz
