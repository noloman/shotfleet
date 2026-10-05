#!/bin/sh
# Build shotfleet for Linux: a folder with the executable and Python inside (like the macOS build, without the Swift OCR
# helper and without signing; `check` reads screenshots with Tesseract there).
#   packaging/build-linux.sh        -> dist/shotfleet/, dist/shotfleet-<version>-linux-<arch>.tar.gz
# Not part of a release yet: there is no Linux installer, and install.sh refuses non-Mac systems. See docs/linux.md.
set -eu
cd "$(dirname "$0")/.."
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
ARCH=$(uname -m)
rm -rf build dist && mkdir -p build
python3 -m venv build/venv
# exact versions, no hashes: requirements-build.txt holds the hashes of the macOS wheels; add a Linux file when Linux ships
build/venv/bin/pip install --quiet pyinstaller==6.22.3 pyinstaller-hooks-contrib==2026.8 certifi==2026.6.17
build/venv/bin/pyinstaller --onedir --name shotfleet --add-data "$PWD/skill:skill" \
  --distpath dist --workpath build/pyi --specpath build --noconfirm --log-level WARN shotfleet.py
dist/shotfleet/shotfleet --version
tar -C dist -czf "dist/shotfleet-$VERSION-linux-$ARCH.tar.gz" shotfleet
sha256sum dist/*.tar.gz
