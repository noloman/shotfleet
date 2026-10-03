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
build/venv/bin/pip install --quiet --upgrade pyinstaller certifi
build/venv/bin/pyinstaller --onedir --name shotfleet --add-data "$PWD/skill:skill" \
  --distpath dist --workpath build/pyi --specpath build --noconfirm --log-level WARN shotfleet.py
dist/shotfleet/shotfleet --version
tar -C dist -czf "dist/shotfleet-$VERSION-linux-$ARCH.tar.gz" shotfleet
sha256sum dist/*.tar.gz
