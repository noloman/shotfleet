#!/bin/sh
# Build shotfleet for Linux: a folder with the executable and Python inside (like the macOS build, without the Swift OCR
# helper and without signing; `check` reads screenshots with Tesseract there).
#   packaging/build-linux.sh        -> dist/shotfleet/, dist/shotfleet-<version>-linux-<arch>.tar.gz
# Not part of a release: there is no Linux installer, and install.sh refuses non-Mac systems. The Docker image (Dockerfile,
# packaging/docker-check.sh) is how Linux gets `check`. See docs/linux.md.
set -eu
cd "$(dirname "$0")/.."
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
ARCH=$(uname -m)
rm -rf build dist && mkdir -p build
python3 -m venv build/venv
# the same hash-checked inputs as the macOS build (requirements-build.txt also holds PyInstaller's Linux wheel hashes)
build/venv/bin/pip install --quiet --only-binary=:all: --require-hashes -r packaging/requirements-build.txt
# the release date (shotfleet.py baked_release_date), frozen into the program like packaging/build.sh does: the build day, in UTC
printf 'RELEASE_DATE = "%s"\n' "$(date -u +%Y-%m-%d)" > build/_release.py
build/venv/bin/pyinstaller --onedir --name shotfleet --add-data "$PWD/skill:skill" --paths "$PWD/build" --hidden-import _release \
  --distpath dist --workpath build/pyi --specpath build --noconfirm --log-level WARN shotfleet.py
dist/shotfleet/shotfleet --version
tar -C dist -czf "dist/shotfleet-$VERSION-linux-$ARCH.tar.gz" shotfleet
sha256sum dist/*.tar.gz
